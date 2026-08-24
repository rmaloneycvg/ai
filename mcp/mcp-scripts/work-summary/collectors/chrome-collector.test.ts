import { describe, it, expect } from "vitest";
import {
  chromeTimeToDate,
  dateToChromeTime,
  classifyUrl,
  buildChromeHistoryPath,
} from "./chrome-collector.js";

// ─── chromeTimeToDate / dateToChromeTime ────────────────────────────────────

describe("Chrome time conversion", () => {
  it("converts Chrome epoch to correct date", () => {
    // Known value: 2026-01-01 00:00:00 UTC in Chrome time
    // Chrome epoch: 1601-01-01, so 2026-01-01 is 425 years later
    const jan1_2026_unix = new Date("2026-01-01T00:00:00Z").getTime();
    const chromeTime = dateToChromeTime(new Date("2026-01-01T00:00:00Z"));
    const backToDate = chromeTimeToDate(chromeTime);
    expect(backToDate.getTime()).toBe(jan1_2026_unix);
  });

  it("round-trips correctly", () => {
    const original = new Date("2026-08-24T15:30:00Z");
    const chromeTime = dateToChromeTime(original);
    const result = chromeTimeToDate(chromeTime);
    expect(result.getTime()).toBe(original.getTime());
  });

  it("handles midnight correctly", () => {
    const midnight = new Date("2026-08-24T00:00:00Z");
    const chromeTime = dateToChromeTime(midnight);
    const result = chromeTimeToDate(chromeTime);
    expect(result.toISOString()).toBe("2026-08-24T00:00:00.000Z");
  });

  it("handles end of day correctly", () => {
    const endOfDay = new Date("2026-08-24T23:59:59.999Z");
    const chromeTime = dateToChromeTime(endOfDay);
    const result = chromeTimeToDate(chromeTime);
    // Within 1ms tolerance due to microsecond rounding
    expect(Math.abs(result.getTime() - endOfDay.getTime())).toBeLessThan(2);
  });

  it("produces positive Chrome time values", () => {
    const now = new Date();
    const chromeTime = dateToChromeTime(now);
    expect(chromeTime > 0n).toBe(true);
  });
});

// ─── classifyUrl ────────────────────────────────────────────────────────────

describe("classifyUrl", () => {
  describe("search detection", () => {
    it("detects Google search", () => {
      const result = classifyUrl("https://www.google.com/search?q=typescript+generics&oq=typescript");
      expect(result.category).toBe("search");
      expect(result.searchQuery).toBe("typescript generics");
    });

    it("detects Bing search", () => {
      const result = classifyUrl("https://www.bing.com/search?q=node.js+streams");
      expect(result.category).toBe("search");
      expect(result.searchQuery).toBe("node.js streams");
    });

    it("detects DuckDuckGo search", () => {
      const result = classifyUrl("https://duckduckgo.com/?q=vitest+mocking&t=h_");
      expect(result.category).toBe("search");
      expect(result.searchQuery).toBe("vitest mocking");
    });

    it("detects Yahoo search", () => {
      const result = classifyUrl("https://search.yahoo.com/search?p=sql+join+syntax");
      expect(result.category).toBe("search");
      expect(result.searchQuery).toBe("sql join syntax");
    });

    it("handles search URL without query param", () => {
      const result = classifyUrl("https://www.google.com/search?oq=test");
      expect(result.category).toBe("search");
      expect(result.searchQuery).toBeUndefined();
    });
  });

  describe("DevTools detection", () => {
    it("detects chrome-devtools:// URLs", () => {
      const result = classifyUrl("chrome-devtools://devtools/bundled/inspector.html");
      expect(result.category).toBe("devtools");
    });

    it("detects devtools://devtools URLs", () => {
      const result = classifyUrl("devtools://devtools/bundled/devtools_app.html");
      expect(result.category).toBe("devtools");
    });

    it("detects chrome://inspect", () => {
      const result = classifyUrl("chrome://inspect/#devices");
      expect(result.category).toBe("devtools");
    });
  });

  describe("general URLs", () => {
    it("classifies regular URLs as general", () => {
      expect(classifyUrl("https://github.com/user/repo").category).toBe("general");
      expect(classifyUrl("https://stackoverflow.com/questions/123").category).toBe("general");
      expect(classifyUrl("https://docs.microsoft.com/en-us/dotnet").category).toBe("general");
    });

    it("does not misclassify Google non-search URLs", () => {
      expect(classifyUrl("https://mail.google.com/mail/").category).toBe("general");
      expect(classifyUrl("https://drive.google.com/drive/").category).toBe("general");
    });
  });
});

// ─── buildChromeHistoryPath ─────────────────────────────────────────────────

describe("buildChromeHistoryPath", () => {
  it("builds correct path for a Windows user", () => {
    const path = buildChromeHistoryPath("ryanm");
    expect(path).toBe("/mnt/c/Users/ryanm/AppData/Local/Google/Chrome/User Data/Default/History");
  });

  it("builds correct path for user with spaces", () => {
    const path = buildChromeHistoryPath("Ryan Maloney");
    expect(path).toContain("Ryan Maloney");
    expect(path).toContain("AppData/Local/Google/Chrome");
  });
});
