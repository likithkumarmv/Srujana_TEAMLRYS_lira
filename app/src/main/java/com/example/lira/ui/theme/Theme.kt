package com.example.lira.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LiraDarkColorScheme = darkColorScheme(
    primary = LiraTealBright,
    onPrimary = Color.Black,
    primaryContainer = LiraTeal,
    onPrimaryContainer = Color.White,
    secondary = LiraEmeraldLight,
    onSecondary = Color.Black,
    surface = LiraSurface,
    onSurface = LiraTextPrimary,
    background = LiraBackground,
    onBackground = LiraTextPrimary,
    error = LiraCrimsonLight,
    onError = Color.Black
)

@Composable
fun LiraTheme(
    darkTheme: Boolean = true, // Authoritative Dark Defense Terminal by default
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = LiraDarkColorScheme,
        typography = Typography,
        content = content
    )
}