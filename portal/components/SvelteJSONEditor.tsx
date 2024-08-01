import { JSONEditor } from 'vanilla-jsoneditor';
import { useEffect, useRef } from 'react';

export default function SvelteJSONEditor(props: any) {
  const refDivContainer = useRef<HTMLDivElement>(null);
  const refEditor = useRef<JSONEditor>();

  useEffect(() => {
    // create editor
    if (refDivContainer?.current) {
      refEditor.current = new JSONEditor({
        target: refDivContainer.current,
        props: {},
      });
    }
  }, []);

  useEffect(() => {
    if (refEditor.current) {
      refEditor.current.updateProps(props);
    }
  }, [props]);

  useEffect(() => {
    return () => {
      // destroy editor
      if (refEditor?.current) {
        refEditor.current?.destroy();
        refEditor.current = undefined;
      }
    };
  }, []);

  return <div className="svelte-jsoneditor-react" ref={refDivContainer}></div>;
}
