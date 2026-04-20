import { resolveRuntimeUrl } from "./api";

export function createRuntimeEventSource(eventsUrl: string): EventSource {
  return new EventSource(resolveRuntimeUrl(eventsUrl));
}
