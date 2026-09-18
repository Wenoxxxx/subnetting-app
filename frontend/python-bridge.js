const { spawn } = require('child_process');

/** Line-delimited JSON bridge to `python -m subnet_calc.cli`. */
class PythonBridge {
  /** @param {string} command python exe or packaged binary */
  constructor(command, args = [], cwd = undefined) {
    this.command = command;
    this.args = args;
    this.cwd = cwd;
    this.pending = [];
    this.buffer = '';
    this.spawnError = null;
    this.proc = spawn(command, args, { cwd });
    this.proc.stdout.on('data', (chunk) => this._onData(chunk));
    this.proc.stderr.on('data', (chunk) => console.error('[python]', chunk.toString()));
    // Spawn failure (e.g. missing python binary) emits 'error', not 'exit'.
    this.proc.on('error', (err) => {
      this.spawnError = err;
      while (this.pending.length) {
        const waiter = this.pending.shift();
        clearTimeout(waiter.timer);
        waiter.reject(err);
      }
    });
    this.proc.on('exit', (code) => {
      const err = new Error(`Python backend exited with code ${code}`);
      while (this.pending.length) {
        const waiter = this.pending.shift();
        clearTimeout(waiter.timer);
        waiter.reject(err);
      }
    });
  }

  _onData(chunk) {
    this.buffer += chunk.toString();
    let idx;
    while ((idx = this.buffer.indexOf('\n')) >= 0) {
      const line = this.buffer.slice(0, idx).trim();
      this.buffer = this.buffer.slice(idx + 1);
      if (!line) continue;
      const waiter = this.pending.shift();
      if (!waiter) continue;
      try {
        clearTimeout(waiter.timer);
        waiter.resolve(JSON.parse(line));
      } catch (err) {
        clearTimeout(waiter.timer);
        waiter.reject(err);
      }
    }
  }

  /**
   * @param {object} request JSON request; resolves to {ok, ...}
   * @param {number} timeoutMs per-request timeout (default 30s); 0 disables
   */
  send(request, timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
      if (this.spawnError) {
        reject(this.spawnError);
        return;
      }
      const waiter = { resolve, reject, timer: null };
      if (timeoutMs > 0) {
        waiter.timer = setTimeout(() => {
          const i = this.pending.indexOf(waiter);
          if (i >= 0) this.pending.splice(i, 1);
          reject(new Error(`Backend timed out after ${timeoutMs}ms`));
        }, timeoutMs);
      }
      this.pending.push(waiter);
      this.proc.stdin.write(JSON.stringify(request) + '\n', (err) => {
        if (err) {
          const i = this.pending.indexOf(waiter);
          if (i >= 0) this.pending.splice(i, 1);
          clearTimeout(waiter.timer);
          reject(err);
        }
      });
    });
  }

  dispose() {
    try {
      this.proc.kill();
    } catch {
      // Already exited; safe to ignore.
    }
  }
}

module.exports = { PythonBridge };
