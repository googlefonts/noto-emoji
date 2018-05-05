# Please note that all these features (except for the Blobmoji EmojiCompat font itself) are now included in their own library which you can find at [FileMojiCompat](FileMojiCompat). This page (and folder) will be updated soon :sweat_smile:
## You can use this font in [EmojiCompat](https://developer.android.com/guide/topics/ui/look-and-feel/emoji-compat.html)!
The most important file for this is `NotoEmojiCompat.ttf`. This is the font you'll need.  
There are three different ways to use this font in EmojiCompat:  
1. Use the `BundledEmojiCompatConfig`:  
   In this case you'll need to put this file with this exact name in your `assets`-folder
2. Use `AssetEmojiCompatConfig`:  
   You can use this config in the same way as `BundledEmojiCompat`.  
   The only difference is that you are able to choose the file name.
3. Use `FileEmojiCompatConfig` (recommended):
   This is the most complex one (well, it isn't actually complex, but you'll need to write a little bit more code).  
   Instead of a `Context` (and an asset name) you'll need to provide either a `File` or a `String` containing the file's name.  
   If your app has neither storage permission nor does it use its own private directory (so this `[Internal storage]/Android/[your.app]/files` directory) it won't work.  
   To make this solution failsafe, you'll need a fallback solution if the font file is not present.  
   One approach is using `AssetEmojiCompatConfig` and the `NoEmojiCompat.ttf` file.  

   Here's an all in one solution I made for [Tusky](https://github.com/tuskyapp/Tusky/pull/600):
   ```java
    /**
     * This method will try to load the emoji font "EmojiCompat.ttf" which should be located at
     * [Internal Storage]/Android/[app.name]/files/EmojiCompat.ttf.
     * If there is no font available it will use a dummy configuration to prevent crashing the app.
     */
    private void initEmojiCompat() {
        // Declaration
        EmojiCompat.Config config;
        // Try to find the font
        File fontFile = new File(getExternalFilesDir(null), "EmojiCompat.ttf");
        if(fontFile.exists()) {
            // It's there!
            config = new FileEmojiCompatConfig(fontFile)
                    // The user probably wants to get a consistent experience
                    .setReplaceAll(true);
        }
        else {
            /*
                If there's no font available, we'll use a minimal fallback font which only
                includes the flags of CN, DE, ES, FR, IT, JP, KR, RU, US.
                However this font won't replace these flags if they are present (which should be the case).
                This has to be done in order to prevent the app from crashing because of an unitialized
                EmojiCompat.
                This fallback is only ~50 kBytes (uncompressed), so it won't add too much bloat.
            */
            config = new AssetEmojiCompatConfig(getApplicationContext(), "NoEmojiCompat.ttf");
        }
        // So we can finally initialize EmojiCompat!
        EmojiCompat.init(config);
    }
   ```
   You can just copy and paste it into your app (which is extremely unprofessional but at least it's easy :sweat_smile:) - no attribution required.

### Why do I recommend the third solution?
The reason for this is same the reason why I made this fork:  
Users should always have a choice - and by using this solution you can give the users of your app the choice to choose their favorite emoji set*!  
Plus they don't rely on you updating your app :smiling_imp:

(*as long as it's available as an EmojiCompat font) 
