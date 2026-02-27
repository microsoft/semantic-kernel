declare module 'openai' {
  class OpenAI {
    constructor(config: any);
    chat: {
      completions: {
        create(options: any): any;
      };
    };
  }
  export default OpenAI;
}
