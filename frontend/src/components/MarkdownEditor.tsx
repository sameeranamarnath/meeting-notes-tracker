import { FC } from "react";
import { Milkdown, useEditor } from "@milkdown/react";
import { defaultValueCtx, Editor, rootCtx } from "@milkdown/core";
import { listener, listenerCtx } from "@milkdown/plugin-listener";
import { commonmark } from "@milkdown/preset-commonmark";
import { history } from "@milkdown/plugin-history";

const defaultContent = `
# Markdown Meeting Note

*Date:* ${new Date().toLocaleDateString()}
*Note taker:* EvesDropp err
*Attendees:*Amar

---

Add notes in Markdown or plain text, as you see fit,
link will be provided on saving for sharing

`;

/**
 * WYSIWYG markdown editor that uses Milkdown.
 * Read more about Milkdown (The WYSIWYG Markdown Editor Framework) here: https://milkdown.dev/
 */
const MarkdownEditor: FC<{
  content: string | null;
  setContent: (text: string) => void;
}> = ({ content, setContent }) => {
  useEditor((root) =>
    Editor.make()
      .config((ctx) => {
        ctx.set(rootCtx, root);
        ctx.set(defaultValueCtx, content || defaultContent);
        ctx.get(listenerCtx).markdownUpdated((_, markdown) => {
          setContent(markdown);
        });
      })
      .use(listener)
      .use(commonmark)
      .use(history)
  );

  return <Milkdown />;
};

export default MarkdownEditor;
