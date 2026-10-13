# Web implementation

Use this reference for CSS or JavaScript/TypeScript changes made through UI Craft's
`build` or `revise` modes, or any other UI implementation. It covers how the code
gets written. The UI Craft contract stays the same: the lock doc, its must-survive
list where the surface already ships, and rendered evidence.

## Establish the baseline

Before selecting syntax, APIs, or CSS features, inspect the project's browser and
support policy, client and server runtime, TypeScript target and libraries,
bundler/transforms, and intentional polyfills. Record the implementation decision
against that baseline.

Keep three questions separate:

1. **ECMAScript standardization:** is the language feature in the standard?
2. **Runtime or host support:** do the target browsers and runtimes provide it?
3. **Transform or polyfill support:** does the toolchain transform it, and is any
   required runtime behavior supplied intentionally?

## Preserve behavior and choose CSS deliberately

Keep async sequencing, concurrency, and cancellation ownership explicit. Preserve
the difference between mutation and change-by-copy, between nullish and other
property states, and between ECMAScript features and browser or host APIs.

For CSS, decide cascade/source order and specificity before adding overrides. Use
Grid for two-dimensional layout and Flexbox for one-dimensional layout; choose
viewport queries for viewport-wide adaptation and container queries for component
adaptation. Prefer logical properties where direction can vary, honor reduced motion
and accessibility needs, and use `@supports` with an explicit fallback or acceptable
degradation when support varies.

Every choice must preserve the lock doc and its must-survive list, and be proven in
the rendered evidence the active UI Craft mode requires. A compatibility claim never
replaces that contract.

## Boundaries and provenance

Do not maintain dated browser or Node matrices, edition snapshots, proposal tables,
or exhaustive feature catalogs here. Check the project baseline and stable primary
standards instead: [ECMA-262](https://tc39.es/ecma262/),
[HTML](https://html.spec.whatwg.org/),
[CSS Cascade](https://www.w3.org/TR/css-cascade-5/), and
[CSS Containment](https://www.w3.org/TR/css-contain-3/).

This is a pack-native synthesis informed by robust-skills contributors (c) 2026:
[modern JavaScript](https://github.com/ccheney/robust-skills/tree/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/modern-javascript)
and [modern CSS](https://github.com/ccheney/robust-skills/tree/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/modern-css).
