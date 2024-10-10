---
runme:
  id: 01J1EP2WP326Y75F96X9XQKSJM
  version: v3
---

As I was studying the documentation markdown files from different repositories, I caught myself to copy-paste some code to a javascript or a typescript file or directly to the browser's dev console or starting a node.js repl. So I thought that it would very convenient to just hit a button and play with the code that I am studying.

```javascript {"id":"01J1EP39QDYNFSMBWYACHT1C76"}

```

So, now users JavaScript Repl extension can start a repl session in a markdown file and evaluate code expressions that are contained inside JavaScript, TypeScript, or CoffeeScript block codes.

```javascript {"id":"01J1EP2WP2T8YREDD2ZYRDZH0X"}
console.log("We ♡ JavaScript!");
```

## Playground for MDN Web Docs and not only

All the times that I have visited the MDN web docs, I always remembered an upcoming feature that I had somewhere in my notes and I would like to support. Although in some of the examples of MDN web you can edit and run the code and see the result this is not happening to most of them and I think that the experience to run these examples through the extension is superior. Users can now browse the MDN Web Docs as markdown files with preview or not and play with code through the extension. You can run the command `JS Repl: Docs` to test it and practice. Users can also practice with the official Typescript, CoffeeScript, Node.js, lodash, RxJS, and Ramda documentation. [Learn more](https://github.com/axilleasiv/vscode-javascript-repl-docs/wiki/Playground-for-MDN-Web)

## Description

Users can create code blocks that could be evaluated by repl extension by placing triple backticks ``` before and after the code block. Usually in most repositories the markdown files in order to have syntax highlighting there is the language identifier after the third backtick, and there is no empty space between the backtick and the language identifier.

\`\`\`javascript

users' code block

\`\`\`

The language identifier is mandatory for the extension in order to evaluate a code block. The language identifiers that are recognized and supported are the following:

- javascript
- js
- jsx
- mjs
- typescript
- ts
- tsx
- coffeescript
- coffee

As users are evaluating code blocks inside a markdown file, by default only one active block is allowed. If there are more than one code block in the visible range of the active block the extension decides which one to activate. If there are mixed code blocks with different languages for example there is one js code block and a ts code block the extension decides which languages to activate and after that which block.

The extension evaluates only one language per time or keystroke and this is the language of the code block that users are editing.

So users can have in the same markdown file javascript, typescript of CoffeeScript code blocks that could be evaluated but only one language per time.

Finally, the users can normally use all the available features of the repl extension for example they can `require` and `import` files or `node_modules` relative to the markdown file path.

### Examples in JavaScript

If a block is not active when the users make the first change then is activated and the extension starts the evaluation.

```js {"id":"01J1EP2WP2T8YREDD300WX8K7P"}
// Try to edit this comment
const obj = {
  language: 'javascript'
}; //=
```

Users can include only the previous block by writing after the language identifier the following `repl-`

```js {"id":"01J1EP2WP2T8YREDD303MW0E51"}
// Try to edit this comment
console.log(obj);

const objNew = {
  language: 'unknown'
}
```

Users can include all the previous blocks that have the same language identifier by adding after the language identifier the `repl--`

```js {"id":"01J1EP2WP2T8YREDD3065BVAGW"}
// Try to edit this comment
console.log(obj);
console.log(objNew);

```

Users can include the next blocks in the same language by adding after the language identifier the `repl++`

```js {"id":"01J1EP2WP2T8YREDD308HGV54K"}
// Try to edit this comment
hello(); /*= */
hello2(); /*= */

```

Maybe users will need to ignore a code block. This can happen by adding after the language identifier the `repl!`

Users can include only the next block in the same language by adding after the language identifier the `repl+`

```js {"id":"01J1EP2WP2T8YREDD309C94AZ2"}
// Try to edit this comment
hello(); /*= */

```

```js {"id":"01J1EP2WP2T8YREDD30C63FPG2"}
function hello() {
  return 'Hello World!';
}
```

The following code block will be ignored

```js {"id":"01J1EP2WP2T8YREDD30CWEJW6W"}
throw new Error('An error!')
```

```js {"id":"01J1EP2WP2T8YREDD30FP6HKYE"}
function hello2() {
  return 'Hello World2!';
}
```

The settings that we have used `repl-`,  `repl--`, `repl+`,  `repl++` and `repl!` are added besides the language identifier, the last setting that can be added besides language identifier is the `repl*` that is used in order to evaluate all the code blocks in the markdown file. If there are more than one language inside the markdown file the language that is selected is depending from the code block that users are editing.

Depending on the case maybe it is not convenient to change this every time per code block, so users can add the following comment `<!-- repl* -->` at the first line of the markdown file.

### Examples in TypeScript

If TypeScript is not installed at the current root folder of the workspace, the latest version of TypeScript will downloaded and installed internally.

```typescript {"id":"01J1EP2WP2T8YREDD30JJTNPZG"}
// Try to edit this comment
function classDecorator<T extends { new (...args: any[]): {} }>(
  constructor: T
) {
  return class extends constructor {
    newProperty = "new property";
    hello = "override";
  };
}

@classDecorator
class Greeter {
  property = "property";
  hello: string;
  constructor(m: string) {
    this.hello = m;
  }
}

console.log(new Greeter("world"));
```

By using the `repl+` identifier the below code block has access to the following block and the function `enumerable`

```ts {"id":"01J1EP2WP2T8YREDD30K4DY2PK"}
// Try to edit this comment
class Greeter {
  greeting: string;
  constructor(message: string) {
    this.greeting = message;
  }

  @enumerable(false)
  greet() {
    return "Hello, " + this.greeting;
  }
}
```

```ts {"id":"01J1EP2WP2T8YREDD30NVE001K"}
function enumerable(value: boolean) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    descriptor.enumerable = value;
  };
}
```

### Examples in CoffeeScript

If CoffeeScript is not installed at the current root folder of the workspace, the latest version of CoffeeScript will downloaded and installed internally.

```coffee {"id":"01J1EP2WP2T8YREDD30SE4RXFB"}
fibonacci = ->
  [previous, current] = [1, 1]
  loop
    [previous, current] = [current, previous + current]
    yield current
  return

getFibonacciNumbers = (length) ->
  results = [1]
  for n from fibonacci()
    results.push n
    break if results.length is length
  results
```

By using the `repl-` identifier the below code block has access to the previous block and the function `getFibonacciNumbers`

```coffee {"id":"01J1EP2WP326Y75F96X5147PR5"}
# Try to edit this comment
console.log(getFibonacciNumbers(4))
```

### Examples in Node.js

```javascript {"id":"01J1EP2WP326Y75F96X67MT5SD"}
// Try to edit this comment
const EventEmitter = require('events');

class MyEmitter extends EventEmitter {}

const myEmitter = new MyEmitter();

myEmitter.on('event', () => {
  console.log('an event occurred!');
});

myEmitter.emit('event');
myEmitter.emit('event');
```

By using the `repl-` identifier the below code block has access to the previous block and the class `MyEmitter`

```js {"id":"01J1EP2WP326Y75F96X8X2TNC3"}
// Try to edit this comment
const myEmitter2 = new MyEmitter();

myEmitter2.on('event', function(a, b) {
  console.log(a, b, this, this === myEmitter);
});

myEmitter2.emit('event', 'a', 'b');
```

