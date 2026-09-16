import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial" });

test("desktop: learn, answer, adapt, save, tutor, import and persist", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /What sparks/ }),
  ).toBeVisible();
  if (process.env.CAPTURE_SCREENSHOTS)
    await page.screenshot({
      path: "test-results/onboarding.png",
      fullPage: true,
    });
  await page.getByRole("button", { name: "Start my learning journey" }).click();
  const active = page.locator(".learning-card.is-active");
  await expect(active).toHaveCount(1);
  await expect(active.getByRole("heading", { level: 2 })).toHaveText(
    "Thinking in Big O",
  );
  if (process.env.CAPTURE_SCREENSHOTS)
    await page.screenshot({
      path: "test-results/desktop-feed.png",
      fullPage: true,
    });
  const initialFeed = await (await request.get("/api/feed?limit=1")).json();
  await active.getByRole("button", { name: "Bookmark card" }).click();
  await expect(
    active.getByRole("button", { name: "Remove bookmark" }),
  ).toBeVisible();
  await active.locator(".why-button").click();
  await expect(
    active.getByText("Why this card?", { exact: true }),
  ).toBeVisible();
  await active
    .getByRole("button", { name: "Close recommendation explanation" })
    .click();
  await active.getByRole("button", { name: "Ask tutor" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page
    .getByRole("button", { name: "Give me an example", exact: true })
    .click();
  await expect(page.locator(".message.assistant")).toContainText(
    "LOCAL STUDY GUIDE",
  );
  await expect(page.locator(".message.assistant")).toContainText(
    /linear|guest list/,
  );
  await page.getByRole("button", { name: "Close tutor" }).click();
  await page.getByRole("tab", { name: "Practice & review" }).click();
  await expect(active.locator(".quiz-options")).toBeVisible();
  const question = await active.locator(".quiz-area h3").innerText();
  if (question.includes("Two separate loops"))
    await active.getByRole("button", { name: /^C O\(n\)$/ }).click();
  else
    await active
      .getByRole("button", { name: "B Doubles", exact: true })
      .click();
  await expect(active.locator(".answer-feedback.success")).toBeVisible();
  const graph = await (await request.get("/api/knowledge")).json();
  expect(
    graph.concepts.find((c: { id: string }) => c.id === "complexity").mastery
      .correct_answers,
  ).toBe(1);
  expect(
    graph.concepts.find((c: { id: string }) => c.id === "binary_search")
      .unlocked,
  ).toBe(true);
  const adapted = await (
    await request.get("/api/feed?limit=1&concept_id=binary_search")
  ).json();
  expect(adapted.cards[0].concept_id).toBe("binary_search");
  expect(initialFeed.cards[0].concept_id).not.toBe("binary_search");
  await page.locator(".main-nav").getByRole("link", { name: "Saved" }).click();
  await expect(
    page.getByRole("heading", { name: "Thinking in Big O", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Revisit" }).click();
  await expect(
    active.getByRole("heading", { name: "Thinking in Big O" }),
  ).toBeVisible();
  // Allow a real visible exposure; page close/navigation must save its duration once.
  await page.clock.install();
  await page.clock.fastForward(15000);
  await page
    .locator(".main-nav")
    .getByRole("link", { name: "Progress" })
    .click();
  await expect(
    page.getByRole("heading", { name: /See how far/ }),
  ).toBeVisible();
  await expect
    .poll(
      async () =>
        (await (await request.get("/api/progress")).json()).total_minutes,
    )
    .toBeGreaterThan(0);
  await page.clock.resume();
  if (process.env.CAPTURE_SCREENSHOTS)
    await page.screenshot({
      path: "test-results/progress.png",
      fullPage: true,
    });
  await page
    .locator(".main-nav")
    .getByRole("link", { name: "Learn", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Knowledge map", exact: true })
    .click();
  await expect(page.locator(".knowledge-map")).toBeVisible();
  await page
    .getByRole("button", { name: "Teach me this", exact: true })
    .click();
  await page.getByLabel("Give your material a title").fill("Queue notes");
  await page
    .getByRole("textbox", { name: "Learning material" })
    .fill(
      "A queue stores values in first-in, first-out order. Enqueue adds to the back, and dequeue removes from the front. A useful example is a line at the checkout.",
    );
  await page
    .getByRole("button", { name: "Create my learning material" })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Your excerpts are ready",
  );
  await page
    .locator(".main-nav")
    .getByRole("link", { name: "Settings" })
    .click();
  await page.getByRole("button", { name: "Light mode", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByRole("button", { name: "AI & usage", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Plenty to learn. No key required." }),
  ).toBeVisible();
  const usage = await (await request.get("/api/usage")).json();
  expect(usage.input_tokens).toBe(0);
  expect(usage.generated_cards).toBe(0);
  await page.getByRole("button", { name: "Preferences", exact: true }).click();
  await page.getByRole("button", { name: "Dark mode", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  expect(errors).toEqual([]);
});

test("mobile: native swipe, previous card and no overflow", async ({
  browser,
}) => {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("http://127.0.0.1:3001/");
  const active = page.locator(".learning-card.is-active");
  await expect(active).toHaveCount(1);
  if (process.env.CAPTURE_SCREENSHOTS)
    await page.screenshot({
      path: "test-results/mobile-feed.png",
      fullPage: true,
    });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(
    await page
      .locator(".learning-card")
      .first()
      .evaluate((el) => el.getBoundingClientRect().bottom),
  ).toBeLessThan(790);
  const title = await active.locator("h2").innerText();
  // Start on the fixed footer so this exercises the outer native snap scroller.
  const footer = await active.locator(".card-footer").boundingBox();
  if (!footer) throw new Error("No footer");
  const cdp = await context.newCDPSession(page);
  const x = 180;
  const y = footer.y + 10;
  await cdp.send("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [{ x, y }],
  });
  for (let delta = 20; delta <= 360; delta += 20)
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchMove",
      touchPoints: [{ x, y: y - delta }],
    });
  await cdp.send("Input.dispatchTouchEvent", {
    type: "touchEnd",
    touchPoints: [],
  });
  await expect(active.locator("h2")).not.toHaveText(title);
  await active
    .getByRole("button", { name: "Previous card", exact: true })
    .click();
  await expect(active.locator("h2")).toHaveText(title);
  await active.getByRole("button", { name: "Ask tutor" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("textbox", { name: "Ask a question" }).fill("Why?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(page.locator(".message.assistant")).toBeVisible();
  await page.getByRole("button", { name: "Close tutor" }).click();
  await page
    .locator(".mobile-nav")
    .getByRole("link", { name: "Learn", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /A path to understanding/ }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
  await context.close();
});

test("flashcard recall and tutor error recovery", async ({ page, request }) => {
  const graph = await (await request.get("/api/knowledge")).json();
  const concept = graph.concepts.find((c: { name: string }) =>
    c.name.startsWith("Queue notes"),
  );
  const feed = await (
    await request.get(`/api/feed?limit=5&concept_id=${concept.id}`)
  ).json();
  const flash = feed.cards.find(
    (c: { type: string }) => c.type === "flashcard",
  );
  expect(flash).toBeTruthy();
  await request.put(`/api/cards/${flash.id}/saved`, { data: { saved: true } });
  await page.goto("/saved");
  const saved = page.locator(".saved-card").filter({ hasText: "Queue notes" });
  await saved.getByRole("button", { name: "Revisit" }).click();
  const active = page.locator(".learning-card.is-active");
  await active.getByRole("button", { name: "Reveal explanation" }).click();
  await expect(active.locator(".flashcard-body")).toContainText(
    "first-in, first-out",
  );
  await active.getByRole("button", { name: "Try recalling again" }).click();
  await expect(
    active.getByRole("button", { name: "Reveal explanation" }),
  ).toBeVisible();
  await active.getByRole("button", { name: "Ask tutor" }).click();
  await page.route("**/api/tutor", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "Temporary tutoring failure. Please retry.",
      }),
    }),
  );
  await page.getByRole("button", { name: "Why?", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
    "Temporary tutoring failure",
  );
  await page.unroute("**/api/tutor");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.locator(".message.assistant")).toContainText(
    "first-in, first-out",
  );
});

test("a long feed session bounds mounted cards and preserves the active card", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const active = page.locator(".learning-card.is-active");
  await expect(active).toHaveCount(1);
  for (let i = 0; i < 65; i++) {
    const before = await active.getAttribute("data-presentation-id");
    const next = page
      .locator(".feed-navigation")
      .getByRole("button", { name: "Next card", exact: true });
    await expect(next).toBeEnabled();
    await next.click();
    await expect(active).not.toHaveAttribute("data-presentation-id", before!);
    await expect(active).toBeInViewport({ ratio: 0.9 });
  }
  expect(await page.locator(".learning-card").count()).toBeLessThanOrEqual(60);
  await expect(
    page
      .locator(".feed-navigation")
      .getByRole("button", { name: "Previous card", exact: true }),
  ).toBeEnabled();
});
