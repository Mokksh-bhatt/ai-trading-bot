-- Create the trades table
CREATE TABLE trades (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  model_name text NOT NULL,
  strategy_tag text NOT NULL,
  asset_class text NOT NULL,
  symbol text NOT NULL,
  entry_price numeric NOT NULL,
  entry_time timestamp with time zone NOT NULL,
  exit_price numeric,
  exit_time timestamp with time zone,
  pnl_pct numeric,
  reasoning_text text NOT NULL,
  confidence numeric NOT NULL
);

-- Index for faster queries
CREATE INDEX idx_trades_model_name ON trades(model_name);
CREATE INDEX idx_trades_symbol ON trades(symbol);
