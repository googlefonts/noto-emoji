# FileMojiCompat
## What is this?
This is a library providing an easy solution to use [EmojiCompat](https://developer.android.com/guide/topics/ui/look-and-feel/emoji-compat) 
with fonts that are either stored in the `assets`-folder with another name than `NotoColorEmojiCompat.ttf` or you can use
EmojiCompat fonts which are stored anywhere on the device's local storage.
## How do I get this library?
That's relatively easy: Just add the following line to your module's `build.gradle` inside `dependencies`:
```
implementation 'de.c1710:filemojicompat:1.0.7'
```
## How do I use it?
There are two different methods included in this library:
1. ### [`AssetEmojiCompatConfig`](https://github.com/C1710/blobmoji/blob/filemojicompat/emojicompat/FileMojiCompat/filemojicompat/src/main/java/de/c1710/filemojicompat/AssetEmojiCompatConfig.java)  
   You can use this just like you would usually use [`BundledEmojiCompatConfig`](https://developer.android.com/guide/topics/ui/look-and-feel/emoji-compat#bundled-fonts)
   except for the detail that you can choose the font's name as the second parameter.  
   Example:
   ```java
   EmojiCompat.Config config = new AssetEmojiCompatConfig(getContext(), "Blobmoji.ttf");
   ```
   This will create a new EmojiCompat configuration using the file provided in `assets/Blobmoji.ttf`.  
   Anyhow, I don't recommend using `AssetEmojiCompatConfig` anymore as [this](#i-want-to-let-my-users-only-choose-another-font-if-they-dont-like-my-current-one) approach is more flexible and just as easy to use.
2. ### [`FileEmojiCompatConfig`](https://github.com/C1710/blobmoji/blob/filemojicompat/emojicompat/FileMojiCompat/filemojicompat/src/main/java/de/c1710/filemojicompat/FileEmojiCompatConfig.java)
   This is the more complex and interesting option.  
   Instead of providing a short String containing the font's name, you can provide a [`File`](https://developer.android.com/reference/java/io/File)
   (or the String containing the full path of it).  
   This will try to load the font from this path.  
   In case it gets into any trouble - let's say because of missing permissions or a non-existent file, it will fallback to using no EmojiCompat at all.  
   (Technically this is wrong as leaving EmojiCompat uninitialized would crash the components using it. There's an explanation below).  
   Example:
   ```java
   Context context = getContext();
   File fontFile = new File(context.getExternalFilesDir(null), "emoji/Blobmoji.ttf");
   EmojiCompat.Config config = new FileEmojiCompatConfig(context, fontFile);
   ```
   In this example, your app would try to load the font file `Blobmoji.ttf` located at `/storage/emulated/0/Android/data/[your.app.package]/files/Blobmoji.ttf`.
   If this file is not available, EmojiCompat won't be visible.  
   Hint: When accessing a file inside your private directory (i.e. the one used in the example), you _don't_ need storage permissions.  
   However, if you want to load the font from somewhere else - let's say the `Download` directory, you ***will*** need storage permissions.  
   But don't worry (too much) - your app won't crash (probably) as this missing file is just being ignored in this case.

### What happens if I don't provide the font file in `FileEmojiCompatConfig`?
In this case, there won't be a visible difference to not using EmojiCompat.  
#### But what does that mean _exactly_?  
If you take a look at `EmojiCompat` itself, you'll notice that it isn't build with missing fonts in mind. If anything happens, 
`onLoadFailed` is called and EmojiCompat crashes - and so do all components relying on it.  
To prevent this case, `FileEmojiCompatConfig` includes a fallback solution - inside the `assets` folder, you'll find a file called [`NoEmojiCompat.ttf`](https://github.com/C1710/blobmoji/blob/filemojicompat/emojicompat/FileMojiCompat/filemojicompat/src/main/assets/NoEmojiCompat.ttf) which
is much smaller than most of the EmojiCompat font files (~40kiB). That's because it only includes 10 characters which are the flags for China, Germany, Spain, France, United Kingdom, Italy, Japan, South Korea, Russia, USA.  
These are the flags which where originally included in [Noto Emoji](https://github.com/googlei18n/noto-emoji) and they are only used to _fill_ the font
file with something.  
#### Will my users see these flags when the fallback font is used?
Yes, they will. But only if their device either doesn't support these flags (which is basically impossible) or if they use a device which already uses
these assets as their default emojis. They won't replace any existing emojis.
#### But I did `setReplaceAll(true)`?!
This won't change anything as `FileEmojiCompatConfig` will detect if the font file is not valid and it will simply ignore `setReplaceAll(true)`.  
## I want to let my users only choose another font if they don't like my current one
This is easily possible with the introduction of `FileMojiCompat 1.0.6`.  
In this case you override the fallback font by putting your font into the `assets` folder of your app using the name `NoEmojiCompat.ttf`.  
Whenever the fallback font is needed (which is the case if the user doesn't specify another one), this font is being used.  
In order to prevent blocking the `setReplaceAll` method, you'll have to call it with `setReplaceAll(true, true)`.  
The second argument indicates that you want to ignore this `replaceAll`-prevention (if set to `true`. Setting it to `false` won't change anything).  
So here's a short example of using this very flexible, yet easy to use method.  
But please be aware that changing the emoji font using this snippet isn't very easy as it needs the user to copy (and potentially rename) some files:
```java
   Context context = getContext();
   File fontFile = new File(context.getExternalFilesDir(null), "emoji.ttf");
   EmojiCompat.Config config = new FileEmojiCompatConfig(context, fontFile)
                                 .setReplaceAll(true, true);
```
In this case, the font specified in `assets/NoEmojiCompat.ttf` will be used until `/storage/emulated/0/Android/[yourpackage]/files/emoji.ttf` exists and includes a valid `EmojiCompat` font.  
This method combines the easy approach of `AssetEmojiCompatConfig` and the flexibility of `FileEmojiCompatConfig` with some tradeoffs on the usability side.  
If you need a different asset path for your fallback file, you can simply add it as another argument for `FileEmojiCompatConfig`. This feature has been introduced in `1.0.7`.  
**_PLEASE use at least this method in your app. It's always better to give the users a choice._**
