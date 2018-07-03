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
     * The default name of the fallback font
     */
    private static final String FONT_FALLBACK = "NoEmojiCompat.ttf";

    /**
     * Creates a new FileEmojiCompatConfig based on an asset.
     * <p/>
     * This means that you can have the flexibility of {@link AssetEmojiCompatConfig}
     * while giving your users the choice to optionally override the font.
     * <p/>
     * The default location for a substituting font is
     * {@code /sdcard/Android/data/your.apps.package/files/EmojiCompat.ttf}.
     *
     * @param context   The app's context is needed for several tasks
     * @param assetPath The path inside the {@code assets} folder for the default font file
     * @return A FileEmojiCompatConfig which will use the given font by default
     */
    public FileEmojiCompatConfig createFromAsset(@NonNull Context context,
                                                 @Nullable String assetPath) {
        if (assetPath != null) {
            FileEmojiCompatConfig config = new FileEmojiCompatConfig(context,
                    new File(context.getExternalFilesDir(null), "EmojiCompat.ttf"),
                    assetPath);
            config.replaceAllOnFallback = true;
            return config;
        } else {
            return createFromAsset(context);
        }
    }

    /**
     * Creates a new FileEmojiCompatConfig based on an asset.
     * <p/>
     * This means that you can have the flexibility of {@link AssetEmojiCompatConfig}
     * while giving your users the choice to optionally override the font.
     * <p/>
     * The default location for a substituting font is
     * {@code /sdcard/Android/data/your.apps.package/files/EmojiCompat.ttf}.
     * <p/>
     * The default name for the Assets font is {@code NoEmojiCompat.ttf}.
     * If you wish to use a different name for this font, please use
     * {@link #createFromAsset(Context, String)}.
     *
     * @param context The app's context is needed for several tasks
     * @return A FileEmojiCompatConfig which will use the given font by default
     */
    public FileEmojiCompatConfig createFromAsset(@NonNull Context context) {
        return createFromAsset(context, FONT_FALLBACK);
    }

    /**
     * Create a new configuration for this EmojiCompat
     * @param path The file name/path of the requested font
     * @param context Context instance
     */
    public FileEmojiCompatConfig(@NonNull Context context,
                                 // NEW
                                 @NonNull String path) {
        // This one is obviously new
        this(context, path, FONT_FALLBACK);
    }

    /**
     * Create a new configuration for this EmojiCompat
     * @param path The file name/path of the requested font
     * @param context Context instance
     * @param fallbackFont The asset path of the fallback font
     */
    public FileEmojiCompatConfig(@NonNull Context context,
                                 // NEW
                                 @NonNull String path,
                                 @Nullable String fallbackFont) {
        // This one is obviously new
        this(context, new File(path), fallbackFont);
    }

    /**
     * Create a new configuration for this EmojiCompat based on a file
     * @param context Context instance
     * @param fontFile The file containing the EmojiCompat font
     */
    public FileEmojiCompatConfig(@NonNull Context context,
                                 // NEW
                                 @Nullable File fontFile) {
        this(context, fontFile, FONT_FALLBACK);
    }

    /**
     * Create a new configuration for this EmojiCompat based on a file
     * @param context Context instance
     * @param fontFile The file containing the EmojiCompat font
     * @param fallbackFont The asset path of the fallback font
     */
    public FileEmojiCompatConfig(@NonNull Context context,
                                 // NEW
                                 @Nullable File fontFile,
                                 @Nullable String fallbackFont) {
        super(new FileMetadataLoader(context,
                fontFile,
                fallbackFont != null ? fallbackFont : FONT_FALLBACK));
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

    /**
     * This is the MetadataLoader. Derived from BundledMetadataLoader but with
     * the addition of a custom file name.
     */
    private static class FileMetadataLoader implements EmojiCompat.MetadataRepoLoader{
        private final Context mContext;
        // NEW
        private final File fontFile;
        private final String fallbackFont;

        private FileMetadataLoader(@NonNull Context context,
                                   // NEW
                                   @Nullable File fontFile,
                                   @NonNull String fallbackFont) {
            this.mContext = context.getApplicationContext();
            // NEW
            this.fontFile = fontFile;
            this.fallbackFont = fallbackFont;
        }


        // Copied from BundledEmojiCompatConfig
        @Override
        @RequiresApi(19)
        public void load(@NonNull EmojiCompat.MetadataRepoLoaderCallback loaderCallback) {
            //Preconditions.checkNotNull(loaderCallback, "loaderCallback cannot be null");
            final InitRunnable runnable = new InitRunnable(mContext, loaderCallback, fontFile, fallbackFont);
            final Thread thread = new Thread(runnable);
            thread.setDaemon(false);
            thread.start();
        }
    }

    @RequiresApi(19)
    private static class InitRunnable implements Runnable {
        // The font names are assigned in the constructor.
        private final File FONT_FILE;
        private final String FONT_FALLBACK;
        // Slightly different variable names
        private final EmojiCompat.MetadataRepoLoaderCallback loaderCallback;
        private final Context context;

        private InitRunnable(final Context context,
                             final EmojiCompat.MetadataRepoLoaderCallback loaderCallback,
                             // NEW parameter
                             final File FONT_FILE,
                             final String FONT_FALLBACK) {
            // This has been changed a bit in order to get some consistency
            this.context = context;
            this.loaderCallback = loaderCallback;
            this.FONT_FILE = FONT_FILE;
            this.FONT_FALLBACK = FONT_FALLBACK;
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
                            MetadataRepo.create(assetManager, FONT_FALLBACK);
                    loaderCallback.onLoaded(resourceIndex);
                } catch (Throwable t2) {
                    Log.e(TAG, "Even the fallback font couldn't be loaded", t2);
                    loaderCallback.onFailed(t);
                }
            }
        }
    }
}
