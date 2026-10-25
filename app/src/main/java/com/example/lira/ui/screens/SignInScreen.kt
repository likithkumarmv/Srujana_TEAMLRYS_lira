package com.example.lira.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.lira.BuildConfig
import com.example.lira.network.StaffAccountException
import com.example.lira.network.SupabaseAuthManager
import com.example.lira.ui.components.PermanentSimulationBanner
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SignInScreen(
    onSignInSuccess: () -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val authErrorFromManager by SupabaseAuthManager.authErrorMessage.collectAsState()
    var email by remember { mutableStateOf("rao@demo.bank") }
    var password by remember { mutableStateOf(BuildConfig.DEMO_PASSWORD) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var staffNoticeDialog by remember { mutableStateOf(false) }

    LaunchedEffect(authErrorFromManager) {
        if (authErrorFromManager != null) {
            errorMessage = authErrorFromManager
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF090D16))
    ) {
        PermanentSimulationBanner()

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Header
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(Color(0xFF0F291E))
                    .border(1.dp, Color(0xFF10B981), RoundedCornerShape(14.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "₹",
                    color = Color(0xFF10B981),
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "DEMO BANK",
                color = Color.White,
                fontSize = 22.sp,
                fontWeight = FontWeight.ExtraBold,
                letterSpacing = 1.sp
            )
            Text(
                text = "Customer App · Powered by LIRA",
                color = Color(0xFF94A3B8),
                fontSize = 13.sp
            )

            Spacer(modifier = Modifier.height(28.dp))

            // Login Box
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF131D2E)),
                shape = RoundedCornerShape(16.dp),
                border = CardDefaults.outlinedCardBorder().copy(brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF26354D)))
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    OutlinedTextField(
                        value = email,
                        onValueChange = { email = it },
                        label = { Text("Customer Email") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFF10B981),
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )

                    OutlinedTextField(
                        value = password,
                        onValueChange = { password = it },
                        label = { Text("Password") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Color(0xFF10B981),
                            unfocusedBorderColor = Color(0xFF334155),
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        )
                    )

                    if (errorMessage != null) {
                        Text(
                            text = errorMessage ?: "",
                            color = Color(0xFFEF4444),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }

                    Button(
                        onClick = {
                            coroutineScope.launch {
                                isLoading = true
                                errorMessage = null
                                val result = SupabaseAuthManager.signIn(email, password)
                                isLoading = false
                                result.onSuccess {
                                    onSignInSuccess()
                                }.onFailure { error ->
                                    if (error is StaffAccountException) {
                                        staffNoticeDialog = true
                                    } else {
                                        errorMessage = error.message ?: "Authentication failed"
                                    }
                                }
                            }
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                        shape = RoundedCornerShape(10.dp),
                        enabled = !isLoading && email.isNotBlank() && password.isNotBlank()
                    ) {
                        if (isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(20.dp),
                                color = Color.White,
                                strokeWidth = 2.dp
                            )
                        } else {
                            Text(
                                text = "Sign In to Demo Bank",
                                color = Color(0xFF042F2E),
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(28.dp))

            // DEMO MODE Section
            Text(
                text = "DEMO MODE · synthetic customers",
                color = Color(0xFF64748B),
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = FontFamily.Monospace,
                letterSpacing = 0.5.sp
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                OutlinedButton(
                    onClick = {
                        email = "rao@demo.bank"
                        password = BuildConfig.DEMO_PASSWORD
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = Color(0xFF1E293B),
                        contentColor = Color(0xFFE2E8F0)
                    ),
                    border = ButtonDefaults.outlinedButtonBorder.copy(
                        brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF334155))
                    )
                ) {
                    Text(
                        text = "Mrs. R. Rao",
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 13.sp
                    )
                }

                OutlinedButton(
                    onClick = {
                        email = "shetty@demo.bank"
                        password = BuildConfig.DEMO_PASSWORD
                    },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        containerColor = Color(0xFF1E293B),
                        contentColor = Color(0xFFE2E8F0)
                    ),
                    border = ButtonDefaults.outlinedButtonBorder.copy(
                        brush = androidx.compose.ui.graphics.SolidColor(Color(0xFF334155))
                    )
                ) {
                    Text(
                        text = "Mr. S. Shetty",
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 13.sp
                    )
                }
            }
        }
    }

    if (staffNoticeDialog) {
        AlertDialog(
            onDismissRequest = { staffNoticeDialog = false },
            title = {
                Text(
                    text = "Access Restricted",
                    color = Color.White,
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Text(
                    text = "Staff use the LIRA Console",
                    color = Color(0xFFCBD5E1),
                    fontSize = 15.sp
                )
            },
            confirmButton = {
                Button(
                    onClick = { staffNoticeDialog = false },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
                ) {
                    Text("OK", color = Color(0xFF042F2E), fontWeight = FontWeight.Bold)
                }
            },
            containerColor = Color(0xFF1E293B)
        )
    }
}
