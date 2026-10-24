package com.moonshang.translator.net

enum class OperatingMode {
    AUTO,
    FORCE_ONLINE,
    FORCE_OFFLINE
}

interface INetworkDetector {
    fun isNetworkConnected(): Boolean
    suspend fun isServerReachable(): Boolean
    suspend fun isOnline(): Boolean
    var mode: OperatingMode
}
