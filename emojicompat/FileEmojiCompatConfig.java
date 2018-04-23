package com.keylesspalace.tusky;
/*
 * Original file (https://android.googlesource.com/platform/frameworks/support/+/master/emoji/bundled/src/main/java/android/support/text/emoji/bundled/BundledEmojiCompatConfig.java):
 *     Copyright (C) 2017 The Android Open Source Project
 * Modifications Copyright (C) 2018 Constantin A.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import android.content.Context;
import android.graphics.Typeface;
import android.support.annotation.NonNull;
import android.support.annotation.RequiresApi;
import android.support.text.emoji.EmojiCompat;
import android.support.text.emoji.MetadataRepo;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;

/**
 * A simple implementation of EmojiCompat.Config using typeface files.
 * Based on:
 * https://android.googlesource.com/platform/frameworks/support/+/master/emoji/bundled/src/main/java/android/support/text/emoji/bundled/BundledEmojiCompatConfig.java
 * Changes are marked with comments. Formatting and other simple changes are not always marked.
 */
public class FileEmojiCompatConfig extends EmojiCompat.Config {
    // The class name is obviously changed from the original file

    /**
     * Create a new configuration for this EmojiCompat
     * @param path The file name/path of the requested font
     * @param context Context instance
     */
    public FileEmojiCompatConfig(@NonNull Context context,
                                 // NEW
                                 @NonNull String path) {
        // This one is obviously new
        super(new FileMetadataLoader(context, path));
    }

    /**
     * This is the MetadataLoader. Derived from BundledMetadataLoader but with
     * the addition of a custom file name.
     */
    private static class FileMetadataLoader implements EmojiCompat.MetadataRepoLoader{
        private final Context mContext;
        // NEW
        private final String fileName;

        private FileMetadataLoader(@NonNull Context context, 
                                    // NEW
                                    String fileName) {
            this.mContext = context.getApplicationContext();
            // NEW
            this.fileName = fileName;
        }


        // Copied from BundledEmojiCompatConfig
        @Override
        @RequiresApi(19)
        public void load(@NonNull EmojiCompat.MetadataRepoLoaderCallback loaderCallback) {
            //Preconditions.checkNotNull(loaderCallback, "loaderCallback cannot be null");
            final InitRunnable runnable = new InitRunnable(mContext, loaderCallback, fileName);
            final Thread thread = new Thread(runnable);
            thread.setDaemon(false);
            thread.start();
        }
    }

    @RequiresApi(19)
    private static class InitRunnable implements Runnable {
        // The font name is assigned in the constructor.
        private final String FONT_NAME;
        // Slightly different variable names
        private final EmojiCompat.MetadataRepoLoaderCallback loaderCallback;
        private final Context context;

        private InitRunnable(final Context context,
                             final EmojiCompat.MetadataRepoLoaderCallback loaderCallback,
                             // NEW parameter
                             final String FONT_NAME) {
            // This has been changed a bit in order to get some consistency
            this.context = context;
            this.loaderCallback = loaderCallback;
            this.FONT_NAME = FONT_NAME;
        }
        
        // This has been copied from BundledEmojiCompatConfig
        @Override
        public void run() {
            try {
                final Typeface typeface = Typeface.createFromFile(FONT_NAME);
                final File fontFile = new File(FONT_NAME);
                final InputStream stream = new FileInputStream(fontFile);
                final MetadataRepo resourceIndex = MetadataRepo.create(typeface, stream);
                loaderCallback.onLoaded(resourceIndex);
            } catch (Throwable t) {
                loaderCallback.onFailed(t);
            }
        }
    }
}
