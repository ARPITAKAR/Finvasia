⚡ I didn’t just use a trading API. I built the execution engine.

Most people place trades.
Some automate strategies.
A few connect APIs and stop there.

I wanted full control — so I built a modular trading engine from scratch.

No black boxes.
No hidden execution.
Just real-time systems, state management, and control over every tick.

🔧 What I built:
- Real-time market feed (WebSocket)
- Signal engine (tick-based logic)
- Trade lifecycle system (open → monitor → exit)
- Paper trading with slippage
- Live execution via broker API
- Thread-safe trade store (no race conditions)
- Risk engine (SL/Target + PnL tracking)
- Telegram alert system
- Strategy framework (multi-leg support)

⚙️ Modes:
- paper → simulated execution
- alert → signal only
- live → real orders

🔄 Flow:
Market → Signal → Risk → Execution → Trade Store → PnL → Exit

⚡ Why this hits different:
Most people use trading systems.
I built one where every trade, decision, and state is fully controlled.

No magic. Just execution.
