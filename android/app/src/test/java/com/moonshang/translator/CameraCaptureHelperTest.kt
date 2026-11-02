package com.moonshang.translator

import android.content.Context
import com.moonshang.translator.camera.CameraCaptureHelper
import io.mockk.every
import io.mockk.mockk
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import java.io.File

class CameraCaptureHelperTest {

    @Test
    fun testCreateTempImageFile(@TempDir tempDir: File) {
        val mockContext = mockk<Context>()
        every { mockContext.cacheDir } returns tempDir

        val file = CameraCaptureHelper.createTempImageFile(mockContext)
        assertNotNull(file)
        assertTrue(file.name.startsWith("photo_"))
        assertTrue(file.name.endsWith(".jpg"))
        assertTrue(file.parentFile?.name == "camera_captures")
    }

    @Test
    fun testCorrectOrientationAndCompressNonExistentFile() {
        val fakeFile = File("/tmp/non_existent_moon_shang_photo.jpg")
        val result = CameraCaptureHelper.correctOrientationAndCompress(fakeFile)
        assertEquals(fakeFile, result)
    }

    @Test
    fun testCorrectOrientationAndCompressEmptyFile(@TempDir tempDir: File) {
        val emptyFile = File(tempDir, "empty.jpg").apply {
            createNewFile()
        }
        val result = CameraCaptureHelper.correctOrientationAndCompress(emptyFile)
        assertEquals(emptyFile, result)
    }
}
