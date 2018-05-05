package de.c1710.filemojicompat;
/*
 * Adapted from https://android.googlesource.com/platform/frameworks/support/+/master/emoji/bundled/src/main/java/android/support/text/emoji/bundled/BundledEmojiCompatConfig.java
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
import android.content.res.AssetManager;
import android.graphics.Typeface;
import android.os.Build;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.support.annotation.RequiresApi;
import android.support.text.emoji.EmojiCompat;
import android.support.text.emoji.MetadataRepo;
import android.util.Log;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.locks.ReentrantLock;

/**
 * A simple implementation of EmojiCompat.Config using typeface files.
 * Based on:
 * https://android.googlesource.com/platform/frameworks/support/+/master/emoji/bundled/src/main/java/android/support/text/emoji/bundled/BundledEmojiCompatConfig.java
 * Changes are marked with comments. Formatting and other simple changes are not always marked.
 */
public class FileEmojiCompatConfig extends EmojiCompat.Config {
    // The class name is obviously changed from the original file
    private final static String TAG = "FileEmojiCompatConfig";

    /**
     * This boolean indicates whether the fallback solution is used.
     */
    private boolean fallback;
    /**
     * Indicates whether all emojis should be replaced when the fallback font is used.
     */
    private boolean replaceAllOnFallback = false;

    /**
     * Create a new configuration for this EmojiCompat
     * @param path The file name/path of the requested font
     * @param context Context instance
     */
    public FileEmojiCompatConfig(@NonNull Context context,
                                 // NEW
                                 @NonNull String path) {
        // This one is obviously new
        this(context, new File(path));
    }

    /**
     * Create a new configuration for this EmojiCompat based on a file
     * @param context Context instance
     * @param fontFile The file containing the EmojiCompat font
     */
    public FileEmojiCompatConfig(@NonNull Context context,
                                 // NEW
                                 @Nullable File fontFile) {
        super(new FileMetadataLoader(context, fontFile));
        if(fontFile != null && fontFile.exists() && fontFile.canRead()) {
            try {
                // Is it a font?
                Typeface typeface = Typeface.createFromFile(fontFile);
                // Is it an EmojiCompat font?
                /*
                    Please note that this will possibly cause a race condition. But all in all it's
                    better to have a chance of detecting such a non-valid font than either having to
                    wait for a long time or not being able to detect it at all.
                    However, since this Thread is started immediately, it should be faster than
                    the initialization process of EmojiCompat itself...
                */
                if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
                    new Thread(() -> {
                        try {
                            MetadataRepo.create(typeface, new FileInputStream(fontFile));
                        } catch (Throwable t) {
                            fallback = true;
                            setReplaceAll(false);
                            Log.w(TAG, "FileEmojiCompatConfig: No valid EmojiCompat font provided. Fallback enabled", t);
                        }
                    }).start();
                }
            } catch (RuntimeException ex) {
                fallback = true;
                Log.e(TAG, "FileEmojiCompatConfig: Font file corrupt. Fallback enabled", ex);
            }
        } else {
            // The heck, this is not even an actual _file_!
            fallback = true;
        }

    }

    @Override
    public FileEmojiCompatConfig setReplaceAll(boolean replaceAll) {
        return setReplaceAll(replaceAll, replaceAllOnFallback);
    }

    /**
     * Replace all emojis
     * @param replaceAll Whether all emojis should be replaced
     * @param replaceAllOnFallback true if this is supposed to be the case even when using the fallback font.
     *                             Useful if the NoEmojiCompat.ttf is overridden by a "real" EmojiCompat font.
     * @return This EmojiCompat.Config
     */
    public FileEmojiCompatConfig setReplaceAll(boolean replaceAll, boolean replaceAllOnFallback) {
        this.replaceAllOnFallback = replaceAllOnFallback;
        if(!fallback || replaceAllOnFallback) {
            super.setReplaceAll(replaceAll);
        }
        else {
            super.setReplaceAll(false);
            if(replaceAll) {
                // If replaceAll would have been set to false anyway, there's no need for apologizing.
                Log.w(TAG, "setReplaceAll: Cannot replace all emojis. Fallback font is active");
            }
        }
        return this;
    }

    private void onFailed() {
        Log.d(TAG, "onFailed: Could not load font");
        fallback = true;
        super.setReplaceAll(false);
    }

    /**
     * This is the MetadataLoader. Derived from BundledMetadataLoader but with
     * the addition of a custom file name.
     */
    private static class FileMetadataLoader implements EmojiCompat.MetadataRepoLoader{
        private final Context mContext;
        // NEW
        private final File fontFile;

        private FileMetadataLoader(@NonNull Context context,
                                   // NEW
                                   @Nullable File fontFile) {
            this.mContext = context.getApplicationContext();
            // NEW
            this.fontFile = fontFile;
        }


        // Copied from BundledEmojiCompatConfig
        @Override
        @RequiresApi(19)
        public void load(@NonNull EmojiCompat.MetadataRepoLoaderCallback loaderCallback) {
            //Preconditions.checkNotNull(loaderCallback, "loaderCallback cannot be null");
            final InitRunnable runnable = new InitRunnable(mContext, loaderCallback, fontFile);
            final Thread thread = new Thread(runnable);
            thread.setDaemon(false);
            thread.start();
        }
    }

    @RequiresApi(19)
    private static class InitRunnable implements Runnable {
        // The font name is assigned in the constructor.
        private final File FONT_FILE;
        // Slightly different variable names
        private final EmojiCompat.MetadataRepoLoaderCallback loaderCallback;
        private final Context context;

        private InitRunnable(final Context context,
                             final EmojiCompat.MetadataRepoLoaderCallback loaderCallback,
                             // NEW parameter
                             final File FONT_FILE) {
            // This has been changed a bit in order to get some consistency
            this.context = context;
            this.loaderCallback = loaderCallback;
            this.FONT_FILE = FONT_FILE;
        }

        @Override
        public void run() {
            try {
                // Changed to load a file
                final Typeface typeface = Typeface.createFromFile(FONT_FILE);
                final InputStream stream = new FileInputStream(FONT_FILE);
                MetadataRepo resourceIndex = MetadataRepo.create(typeface, stream);
                loaderCallback.onLoaded(resourceIndex);
            }
            catch (Throwable t) {
                // Instead of crashing, this one will first try to load the fallback font
                try {
                    android.util.Log.w(TAG, "Error while loading the font file.", t);
                    final AssetManager assetManager = context.getAssets();
                    final MetadataRepo resourceIndex =
                            MetadataRepo.create(assetManager, "NoEmojiCompat.ttf");
                    loaderCallback.onLoaded(resourceIndex);
                } catch (Throwable t2) {
                    loaderCallback.onFailed(t);
                }
            }
        }

        interface EmojiFontFailListener {
            void onFailed();
        }
    }
}
