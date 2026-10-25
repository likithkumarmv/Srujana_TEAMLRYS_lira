package com.example.lira

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.lifecycleScope
import com.example.lira.data.PaymentItem
import com.example.lira.data.SyncRepository
import com.example.lira.network.SupabaseAuthManager
import com.example.lira.ui.screens.*
import com.example.lira.ui.theme.LiraTheme

enum class Screen {
    SIGN_IN,
    HOME,
    SEND_MONEY,
    PAUSED,
    RESULT,
    TRUSTED_PERSON,
    ACTIVITY
}

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            LiraTheme {
                var currentScreen by remember {
                    mutableStateOf(if (SupabaseAuthManager.isSignedIn()) Screen.HOME else Screen.SIGN_IN)
                }
                var activePayment by remember { mutableStateOf<PaymentItem?>(null) }

                val authenticatedEmail by SupabaseAuthManager.authenticatedEmail.collectAsState()
                LaunchedEffect(authenticatedEmail) {
                    if (authenticatedEmail == null && currentScreen != Screen.SIGN_IN) {
                        SyncRepository.stopForegroundSync()
                        currentScreen = Screen.SIGN_IN
                    }
                }

                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color(0xFF090D16))
                ) {
                    when (currentScreen) {
                        Screen.SIGN_IN -> {
                            SignInScreen(
                                onSignInSuccess = {
                                    SyncRepository.startForegroundSync(lifecycleScope)
                                    currentScreen = Screen.HOME
                                }
                            )
                        }

                        Screen.HOME -> {
                            HomeScreen(
                                onNavigateToSend = { currentScreen = Screen.SEND_MONEY },
                                onNavigateToActivity = { currentScreen = Screen.ACTIVITY },
                                onNavigateToTrustedPerson = { currentScreen = Screen.TRUSTED_PERSON },
                                onNavigateToPaused = { item ->
                                    activePayment = item
                                    currentScreen = Screen.PAUSED
                                },
                                onNavigateToResult = { item ->
                                    activePayment = item
                                    currentScreen = Screen.RESULT
                                },
                                onSignOut = {
                                    SyncRepository.stopForegroundSync()
                                    currentScreen = Screen.SIGN_IN
                                }
                            )
                        }

                        Screen.SEND_MONEY -> {
                            SendMoneyScreen(
                                onNavigateBack = { currentScreen = Screen.HOME },
                                onNavigateToPaused = { item ->
                                    activePayment = item
                                    currentScreen = Screen.PAUSED
                                },
                                onNavigateToResult = { item ->
                                    activePayment = item
                                    currentScreen = Screen.RESULT
                                }
                            )
                        }

                        Screen.PAUSED -> {
                            activePayment?.let { payment ->
                                PausedScreen(
                                    initialPayment = payment,
                                    onNavigateBack = { currentScreen = Screen.HOME },
                                    onNavigateToResult = { updated ->
                                        activePayment = updated
                                        currentScreen = Screen.RESULT
                                    }
                                )
                            } ?: run {
                                currentScreen = Screen.HOME
                            }
                        }

                        Screen.RESULT -> {
                            activePayment?.let { payment ->
                                ResultScreen(
                                    payment = payment,
                                    onNavigateHome = {
                                        activePayment = null
                                        currentScreen = Screen.HOME
                                    }
                                )
                            } ?: run {
                                currentScreen = Screen.HOME
                            }
                        }

                        Screen.TRUSTED_PERSON -> {
                            TrustedPersonScreen(
                                onNavigateBack = { currentScreen = Screen.HOME }
                            )
                        }

                        Screen.ACTIVITY -> {
                            ActivityScreen(
                                onNavigateBack = { currentScreen = Screen.HOME },
                                onNavigateToPaused = { item ->
                                    activePayment = item
                                    currentScreen = Screen.PAUSED
                                },
                                onNavigateToResult = { item ->
                                    activePayment = item
                                    currentScreen = Screen.RESULT
                                }
                            )
                        }
                    }
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        if (SupabaseAuthManager.isSignedIn()) {
            SyncRepository.startForegroundSync(lifecycleScope)
        }
    }

    override fun onStop() {
        super.onStop()
        SyncRepository.stopForegroundSync()
    }
}