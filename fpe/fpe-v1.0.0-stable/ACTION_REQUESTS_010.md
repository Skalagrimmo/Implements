# FPE 0.10 semantic action requests

FPE 0.10 adds a one-way semantic request envelope without granting FPE authority to mutate PixelGen state.

```js
const req = runtime.request('inspect', 'sector_0_0', {
  mode: 'deep'
});
```

The returned object uses schema `fpe.action_request/0.10.0` and contains:

- `action`: trimmed host-defined action name (1–64 characters)
- `target`: an existing FPE `cluster` or `bud` id with explicit target kind
- `payload`: detached JSON-compatible plain data supplied by the caller
- `source`: PixelGen world fingerprint, seed, dimensions, state revision and state tick from the currently accepted projection

The request is a description of intent only. FPE does not execute the action, decide whether the action is legal, or write any resulting state back. The authoritative host/PixelGen layer must validate the action and, if accepted, produce a new state/projection which can later enter FPE through `accept()`.

## Validation

`request()` rejects empty/oversized action names, missing targets, arrays as the top-level payload, non-finite numbers, functions, `undefined`, non-plain objects, cyclic values, and nesting deeper than 32 levels. Unknown target IDs use the existing `UNKNOWN_ID` code; malformed request data uses `INVALID_REQUEST`.

Returned envelopes are detached from runtime state. Mutating a request object cannot mutate FPE projection, view, or future requests.

## Authority boundary

```text
user/UI intent
    ↓
FPE request()  ── creates immutable-by-ownership intent data only
    ↓
authoritative host / PixelGen validation + apply
    ↓
new PixelGen state
    ↓
bridge → projection
    ↓
FPE accept()
```

There is still no direct semantic writeback path inside FPE.
