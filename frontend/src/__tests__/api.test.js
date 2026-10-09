import {describe, it, expect, vi, beforeEach, afterEach} from 'vitest';
import {streamAnswer, ApiError} from '../lib/api.js';

const mockStream = (frames) => {
  const encoder = new TextEncoder();
  return {
    ok: true,
    status: 200,
    body: new ReadableStream({
      start(controller) {
        for (const frame of frames) controller.enqueue(encoder.encode(`data: ${JSON.stringify(frame)}\n\n`));
        controller.close();
      },
    }),
  };
};

describe('streamed AI events', () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('preserves server token chunks and stops only on done', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(mockStream([
      {type: 'init', conversation_id: 'chat-test'},
      {type: 'token', content: 'Real '},
      {type: 'token', content: 'response'},
      {type: 'done'},
    ])));
    const received = [];
    await streamAnswer({text:'Hello',mode:'coding'}, (event) => received.push(event));
    expect(received.map((item) => item.type)).toEqual(['init','token','token','done']);
  });

  it('rejects a stream ending without done', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(mockStream([
      {type:'init',conversation_id:'chat-test'},
      {type:'token',content:'Incomplete'},
    ])));
    await expect(streamAnswer({text:'Hello',mode:'coding'}, () => {})).rejects.toThrow('before completion');
  });

  it('treats server error events as failures rather than successful answers', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(mockStream([
      {type:'init',conversation_id:'chat-test'},
      {type:'error',content:'AI unavailable'},
    ])));
    await expect(streamAnswer({text:'Hello',mode:'coding'}, () => {})).rejects.toMatchObject({status:503});
  });
});
