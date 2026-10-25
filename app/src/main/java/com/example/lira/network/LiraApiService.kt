package com.example.lira.network

import com.example.lira.data.*
import retrofit2.Response
import retrofit2.http.*

interface LiraApiService {
    @GET("sync/version")
    suspend fun getSyncVersion(): SyncVersionResponse

    @GET("me")
    suspend fun getMe(@Header("x-customer-email") email: String? = null): CustomerProfile

    @GET("me/payments")
    suspend fun getPayments(@Header("x-customer-email") email: String? = null): kotlinx.serialization.json.JsonElement

    @POST("payments")
    suspend fun createPayment(
        @Body req: PaymentCreateRequest,
        @Header("x-customer-email") email: String? = null
    ): Response<kotlinx.serialization.json.JsonElement>

    @POST("cases/{id}/cancel")
    suspend fun cancelCase(
        @Path("id") id: String,
        @Body req: CancelRequest
    ): Response<CancelResponse>

    @POST("reconfirm")
    suspend fun reconfirmPayment(
        @Body req: ReconfirmRequest
    ): Response<ReconfirmResponse>

    @POST("help")
    suspend fun requestHelp(
        @Body req: HelpRequest
    ): Response<HelpResponse>

    @POST("trusted")
    suspend fun updateTrustedPerson(
        @Body req: TrustedPersonRequest
    ): Response<HelpResponse>

    @GET("payees")
    suspend fun getPayees(): PayeeListResponse
}
