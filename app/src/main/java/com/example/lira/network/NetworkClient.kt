package com.example.lira.network

import com.example.lira.BuildConfig
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit

object NetworkClient {

    val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
        coerceInputValues = true
    }

    private val okHttpClient: OkHttpClient by lazy {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        OkHttpClient.Builder()
            .connectTimeout(5, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .addInterceptor { chain ->
                val original = chain.request()
                try {
                    val builder = original.newBuilder()

                    // Add Authorization Bearer only if valid JWT
                    SupabaseAuthManager.getAccessToken()?.let { token ->
                        if (SupabaseAuthManager.isValidJwt(token)) {
                            builder.header("Authorization", "Bearer $token")
                        }
                    }

                    // Add active customer email header
                    SupabaseAuthManager.authenticatedEmail.value?.let { email ->
                        builder.header("X-Customer-Email", email)
                    }

                    var response = chain.proceed(builder.build())

                    // 401 Session Refresh
                    if (response.code == 401) {
                        response.close()
                        SupabaseAuthManager.clearToken()
                        val newToken = runBlocking { SupabaseAuthManager.refreshTokenOrDemo() }
                        if (newToken != null && SupabaseAuthManager.isValidJwt(newToken)) {
                            val newRequest = original.newBuilder().apply {
                                header("Authorization", "Bearer $newToken")
                                SupabaseAuthManager.authenticatedEmail.value?.let { email ->
                                    header("X-Customer-Email", email)
                                }
                            }.build()
                            response = chain.proceed(newRequest)
                        }
                        if (response.code == 401) {
                            runBlocking {
                                SupabaseAuthManager.signOut("Please sign in again")
                            }
                        }
                    }

                    response
                } catch (e: Exception) {
                    android.util.Log.e("LIRA_NET", "Request to ${original.url} failed: ${e.message}", e)
                    throw e
                }
            }
            .addInterceptor(logging)
            .build()
    }

    val apiService: LiraApiService by lazy {
        val rawBase = BuildConfig.API_BASE_URL.trim()
        val normalized = if (rawBase.endsWith("/")) rawBase else "$rawBase/"
        val mediaType = "application/json".toMediaType()

        Retrofit.Builder()
            .baseUrl(normalized)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory(mediaType))
            .build()
            .create(LiraApiService::class.java)
    }
}
