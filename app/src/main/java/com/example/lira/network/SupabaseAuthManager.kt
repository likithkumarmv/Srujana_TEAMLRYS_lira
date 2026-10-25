package com.example.lira.network

import android.util.Log
import com.example.lira.BuildConfig
import com.example.lira.data.DemoTokenRequest
import com.example.lira.data.DemoTokenResponse
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.Auth
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.auth.providers.builtin.Email
import io.github.jan.supabase.createSupabaseClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

class StaffAccountException(message: String = "Staff use the LIRA Console") : Exception(message)

object SupabaseAuthManager {
    private const val TAG = "SupabaseAuthManager"

    val supabase: SupabaseClient = createSupabaseClient(
        supabaseUrl = BuildConfig.SUPABASE_URL,
        supabaseKey = BuildConfig.SUPABASE_ANON_KEY
    ) {
        install(Auth)
    }

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }

    private val directHttpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(5, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .build()
    }

    private val _authenticatedEmail = MutableStateFlow<String?>(null)
    val authenticatedEmail: StateFlow<String?> = _authenticatedEmail.asStateFlow()

    private val _authenticatedRole = MutableStateFlow<String?>("CUSTOMER")
    val authenticatedRole: StateFlow<String?> = _authenticatedRole.asStateFlow()

    private val _cachedToken = MutableStateFlow<String?>(null)
    private val _tokenSource = MutableStateFlow<String?>(null)

    private val _authErrorMessage = MutableStateFlow<String?>(null)
    val authErrorMessage: StateFlow<String?> = _authErrorMessage.asStateFlow()

    fun isValidJwt(token: String?): Boolean {
        if (token.isNullOrBlank()) return false
        val parts = token.split(".")
        return parts.size == 3 && parts.all { it.isNotBlank() }
    }

    fun clearToken() {
        _cachedToken.value = null
    }

    fun clearAuthErrorMessage() {
        _authErrorMessage.value = null
    }

    private fun mapToDemoEmail(input: String): String {
        val lower = input.lowercase()
        return when {
            lower.contains("rao") -> "rao@demo.bank"
            lower.contains("shetty") -> "shetty@demo.bank"
            lower.contains("officer1") -> "officer1@demo.bank"
            lower.contains("officer2") -> "officer2@demo.bank"
            lower.contains("analyst") -> "analyst@demo.bank"
            lower.contains("admin") -> "admin@demo.bank"
            else -> input
        }
    }

    suspend fun fetchDemoToken(email: String, pass: String): DemoTokenResponse? = withContext(Dispatchers.IO) {
        val rawBase = BuildConfig.API_BASE_URL.trim()
        val base = if (rawBase.endsWith("/")) rawBase else "$rawBase/"
        val url = "${base}demo/token"

        suspend fun attempt(targetEmail: String): DemoTokenResponse? {
            return try {
                val reqBody = json.encodeToString(
                    DemoTokenRequest.serializer(),
                    DemoTokenRequest(email = targetEmail, password = pass)
                )
                val request = Request.Builder()
                    .url(url)
                    .post(reqBody.toRequestBody("application/json".toMediaType()))
                    .build()

                directHttpClient.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        val bodyStr = response.body?.string() ?: return null
                        json.decodeFromString(DemoTokenResponse.serializer(), bodyStr)
                    } else {
                        Log.w(TAG, "POST /demo/token for $targetEmail returned HTTP ${response.code}")
                        null
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed calling /demo/token for $targetEmail: ${e.message}", e)
                null
            }
        }

        // 1. Try with the entered email
        var res = attempt(email)
        if (res != null && isValidJwt(res.accessToken)) {
            return@withContext res
        }

        // 2. Try mapped demo email if distinct
        val mapped = mapToDemoEmail(email)
        if (mapped != email) {
            res = attempt(mapped)
            if (res != null && isValidJwt(res.accessToken)) {
                return@withContext res
            }
        }

        null
    }

    suspend fun signIn(email: String, pass: String): Result<String> {
        val trimmedEmail = email.trim()
        val trimmedPass = pass.trim()
        _authErrorMessage.value = null

        return runCatching {
            var token: String? = null
            var role: String = "CUSTOMER"
            var source = "supabase"

            // 1. Try Supabase email sign-in first
            try {
                supabase.auth.signInWith(Email) {
                    this.email = trimmedEmail
                    this.password = trimmedPass
                }
                val currentSession = supabase.auth.currentSessionOrNull()
                val sbToken = currentSession?.accessToken
                if (isValidJwt(sbToken)) {
                    token = sbToken
                    source = "supabase"
                    val user = supabase.auth.currentUserOrNull()
                    val metaRole = (user?.userMetadata?.get("role") as? String)
                        ?: (user?.appMetadata?.get("role") as? String)
                    if (metaRole != null) {
                        role = metaRole.uppercase()
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Supabase sign in failed (${e.message}), attempting demo token fallback")
            }

            // 2. Fallback to POST /demo/token if no valid JWT available
            if (token == null || !isValidJwt(token)) {
                val demoResult = fetchDemoToken(trimmedEmail, trimmedPass)
                if (demoResult != null && isValidJwt(demoResult.accessToken)) {
                    token = demoResult.accessToken
                    source = "demo"
                    demoResult.role?.let { role = it.uppercase() }
                }
            }

            // 3. Reject if no valid JWT could be obtained
            if (token == null || !isValidJwt(token)) {
                _authenticatedEmail.value = null
                _cachedToken.value = null
                _tokenSource.value = null
                throw Exception("Sign-in failed: Unable to obtain valid session token from server.")
            }

            // 4. Role check
            val isStaff = trimmedEmail.contains("officer", ignoreCase = true) ||
                    trimmedEmail.contains("analyst", ignoreCase = true) ||
                    role != "CUSTOMER"

            if (isStaff) {
                signOut()
                throw StaffAccountException("Staff use the LIRA Console")
            }

            _authenticatedEmail.value = trimmedEmail
            _authenticatedRole.value = role
            _cachedToken.value = token
            _tokenSource.value = source

            val parts = token.split(".").size
            Log.d("LIRA_AUTH", "token source=$source, parts=$parts")
            Log.i("LIRA_AUTH", "token source=$source, parts=$parts")
            println("LIRA_AUTH: token source=$source, parts=$parts")

            trimmedEmail
        }
    }

    suspend fun refreshTokenOrDemo(): String? {
        val currentEmail = _authenticatedEmail.value ?: return null

        // 1. Try Supabase refresh if originally from Supabase
        if (_tokenSource.value == "supabase") {
            try {
                supabase.auth.refreshCurrentSession()
                val token = supabase.auth.currentSessionOrNull()?.accessToken
                if (isValidJwt(token)) {
                    _cachedToken.value = token
                    val parts = token!!.split(".").size
                    Log.d("LIRA_AUTH", "token source=supabase, parts=$parts")
                    return token
                }
            } catch (e: Exception) {
                Log.w(TAG, "Supabase session refresh failed: ${e.message}")
            }
        }

        // 2. Fallback to /demo/token
        val demoRes = fetchDemoToken(currentEmail, BuildConfig.DEMO_PASSWORD)
        if (demoRes != null && isValidJwt(demoRes.accessToken)) {
            _cachedToken.value = demoRes.accessToken
            _tokenSource.value = "demo"
            val parts = demoRes.accessToken.split(".").size
            Log.d("LIRA_AUTH", "token source=demo, parts=$parts")
            Log.i("LIRA_AUTH", "token source=demo, parts=$parts")
            println("LIRA_AUTH: token source=demo, parts=$parts")
            return demoRes.accessToken
        }

        _cachedToken.value = null
        return null
    }

    suspend fun refreshSession(): String? = refreshTokenOrDemo()

    suspend fun signOut(errorMessage: String? = null) {
        try {
            supabase.auth.signOut()
        } catch (_: Exception) {}
        _authenticatedEmail.value = null
        _authenticatedRole.value = null
        _cachedToken.value = null
        _tokenSource.value = null
        _authErrorMessage.value = errorMessage
    }

    fun getAccessToken(): String? = _cachedToken.value ?: supabase.auth.currentSessionOrNull()?.accessToken

    fun isSignedIn(): Boolean = _authenticatedEmail.value != null && isValidJwt(getAccessToken())
}
