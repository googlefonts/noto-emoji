package de.c1710.filemojicompat;
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
import android.content.res.AssetManager;
import android.support.annotation.NonNull;
import android.support.annotation.RequiresApi;
import android.support.text.emoji.EmojiCompat;
import android.support.text.emoji.MetadataRepo;

/**
 * A simple implementation of EmojiCompat.Config using typeface assets.
 * Based on:
 * https://android.googlesource.com/platform/frameworks/support/+/master/emoji/bundled/src/main/java/android/support/text/emoji/bundled/BundledEmojiCompatConfig.java
 * Changes are marked with comments. Formatting and other simple changes are not always marked.
 *
 * @deprecated Please use {@link FileEmojiCompatConfig#createFromAsset(Context, String)} instead
 * for greater flexibility.
 */
@Deprecated
public class AssetEmojiCompatConfig extends EmojiCompat.Config {
    // The class name is obviously changed from the original file

    /**
     * Create a new configuration for this EmojiCompat
     *
     * @param assetName The file name/path of the requested font
     * @param context   Context instance
     */
    public AssetEmojiCompatConfig(@NonNull Context context,
                                  // NEW
                                  @NonNull String assetName) {
        // This one is oviously new
        super(new AssetMetadataLoader(context, assetName));
    }

    /**
     * This is the MetadataLoader. Derived from BundledMetadataLoader but with
     * the addition of a custom asset name.
     */
    private static class AssetMetadataLoader implements EmojiCompat.MetadataRepoLoader {
        private final Context mContext;
        // NEW
        private final String assetName;

        private AssetMetadataLoader(@NonNull Context context,
                                    // NEW
                                    String assetName) {
            this.mContext = context.getApplicationContext();
            // NEW
            this.assetName = assetName;
        }


        // Copied from BundledEmojiCompatConfig
        @Override
        @RequiresApi(19)
        public void load(@NonNull EmojiCompat.MetadataRepoLoaderCallback loaderCallback) {
            // This one doesn't work as it's not android.support
            //Preconditions.checkNotNull(loaderCallback, "loaderCallback cannot be null");
            final InitRunnable runnable = new InitRunnable(mContext, loaderCallback, assetName);
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
                final AssetManager assetManager = context.getAssets();
                final MetadataRepo resourceIndex = MetadataRepo.create(assetManager, FONT_NAME);
                loaderCallback.onLoaded(resourceIndex);
            } catch (Throwable t) {
                loaderCallback.onFailed(t);
            }
        }
    }
}
