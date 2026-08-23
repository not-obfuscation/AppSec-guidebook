// Тест-кейсы того же правила на втором стеке: TypeScript и идиома React.
// Разметка та же: // ruleid: и // ok:.

declare const window: Window;
declare function useEffect(fn: () => void | (() => void), deps: unknown[]): void;
declare function applySettings(v: unknown): void;
declare function isTrusted(origin: string): boolean;

type Settings = { theme: string };

// Обработчик объявлен рядом и передан по имени — тела в точке подписки нет.
export function WidgetHostBadExample(): void {
  const onMessage = (event: MessageEvent): void => {
    applySettings(JSON.parse(event.data as string) as Settings);
  };
  useEffect(() => {
    // ruleid: postmessage-handler-by-name
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, []);
}

// Тот же дефект, но подписка на месте: тело видно, origin не читается.
export function WidgetHostInline(): void {
  useEffect(() => {
    // ruleid: postmessage-no-origin-check
    window.addEventListener('message', (event: MessageEvent): void => {
      applySettings(JSON.parse(event.data as string) as Settings);
    });
  }, []);
}

// Исправленный вариант на том же стеке.
export function WidgetHostFixed(): void {
  useEffect(() => {
    // ok: postmessage-no-origin-check
    window.addEventListener('message', (event: MessageEvent): void => {
      if (!isTrusted(event.origin)) return;
      applySettings(JSON.parse(event.data as string) as Settings);
    });
  }, []);
}
