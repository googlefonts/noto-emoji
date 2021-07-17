FROM ghcr.io/c1710/emoji_builder

COPY svg ./svg
COPY third_party/region-flags/svg ./flags
COPY emoji_aliases.txt NotoColorEmoji.tmpl.ttx.tmpl Blobmoji.gpl ./
COPY AUTHORS CONTRIBUTORS CHANGES.md LICENSE ./

VOLUME /build
VOLUME /output

CMD /github_workflow_setup.sh && \
	/bin/emoji_builder -vv -b /build -o Blobmoji.ttf -O /output --flags ./flags blobmoji -w -a ./emoji_aliases.txt --ttx-tmpl ./NotoColorEmoji.tmpl.ttx.tmpl --palette ./Blobmoji.gpl && \
	mv /output/Blobmoji_win.ttf /output/BlobmojiWindows.ttf