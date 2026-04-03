NAME: Price Action Cycle

worth checking markets.news for news info (maybe parsing once per hour or so) or other source of news

INSTRUMENTS: 
CFD
    XAUUSD
    USOIL (WTIUSD, WTI.fs) - here we need to be aware of geopolitical situation
    US500
    US30
    USTECH
    GBPUSD
    EURUSD
    BTCUSD
FUTURES
    NAS100
    GC
    CL
    ES
    NQ
    YM
    6E

We need to observe what events affect more gold what btc and other cfd/futures etc.
CHART:M5 (but we prefer Tickchart. afair we generate it dynamically but need to confirm how it will slow down the ea)
Regarding tick chart. I have a tick chart generator for mt4, maybe it's worth

at 13-14 Polish time the tick chart should show 150-160 candles from midnight till 13-14 so we need to adjust the candle size for it

SIGNAL CANDLE
    WICK below body for BULLISH
    WICK above body for BEARISH
    Impulse pullback signal
    we want them to allign with EMA or volume or S/R lines or clusters, zones, fibo zones etc.

GAP CANDLE
    reversed to SIGNAL CANDLE 
    those candles create lines that price tend to retest
    

TRENDLINES (I'm sure there are quite few coded options in the internet to how to do it properly)
    a line used to find "Direction of trend"
    Trend lines determine S/R levels

    TO MAKE IT PROPERLY
    1. Use first 2 swings LOW or HIGH (it can make a channel together)
    2. Try to grab together WICKS

    We might adjust it later when market shifts to consolidation of changes the direction

    there are 3 types of trednlines
    MAJOR - 1-2 per day depends
    MINOR - 3-5 per day
    MICRO - quite a lot it can be 15 or 20 or more


MOVING AVERAGES

    EMA21 - used for intraday trades
    SMA61 - used for swing trading
    
    It allows us to determine markets sentiment
    If price is above ema21 and SMA61 then we can say that market has bullish sentiment
    vice versa for bearish sentiment

    If the price is between Moving Averages this means that the sentiment is ending and we need to be more flexible

    the point of ema crossing sma can be seen as Switch in sentiment

When the trend and sentiment is BULLISH so we are looking for BULLISH SIGNAL CANDLE
It's important to observe how the price "work" (cross it and goes back or bounce from it) with the average and if the signal candle shows

If the price crosses both averages in a DYNAMIC way(1-5 M5 candles) we ca take values of crossing EMA21 and SMA61 as range as S/R which we can expect that will be retested and continue the trend

FIBO LEVELS
    Traders use fibonacci levels to find best spot for pullback
    38.2, 61.8, 1.382, 1.618 as GOLDEN RATIO MOST COMMONLY USED

    There are EXTENSIONS (AB) and EXPANSIONS (ABC)
    another way to determine S/R
    
    EXTENSIONS
        Where 
            A - beginning of the impulse (to some direction) (we need to find in the internet how to identify the impulse) The impulse needs to be "visible", we do not add new story to some small movements
            B - end of impulse
        38.2 - 61.8 -> pullback zones. Support zone. In this zone price will test it after the impulse. The correction has to be visible. If the correction is only "gentle" we can expect another dip. If the behavior is "random" we look for other opportunities.
        1.382 - 1.618 -> pullback zone. resistance zone.

    EXPANSIONS
        Where
            A - beginning of the impulse (to some direction) (we need to find in the internet how to identify the impulse)
            B - end of impulse
            C - dip of the correction. How deep into the correction the price went. If the next correction will be deeper then we need to recalculate it
        38.2
        61.8
        1 - measured-move  
        1.382
        1.618
        Goal of expansions is for price to reach Measured-Move or 1.382 or 1.618
    
    WITH THOSE VALUES AND LEVELS WE CAN MAKE CLUSTERS (~5 pips)

    The values, levels cluster are the context of our trade

    In case when we want to make an order, places like reaction to impulse or reaction to cluster etc might be a good place to place an order (of course we need a signal candle)

ELLIOTT WAVES
    M5 
    When we observe change in sentiment we are not sure if the trend is shifting
    3 - 5 (in some cases it can be more) waves (movements, or impulses) is a full trend. Between impulses, movements there are similar but oposite direction impulses
    2 or 3 of same movement -> pullback
    if we are in 4th and 5th impulse we shouldn't force to trade

REVERSAL LINES
    From support to resistance
    we mark latest swing high/low (wick)
    if we see a reaction to the level/zone marked by the swing then we can mark it
    if no we just omit the swing
    that way we can make a S/R zones
    Those zones, reactions mix with trendlines (major and minor, NOT MICRO)

DOUBLE TOP&BOTTOM (M5)
    If market moved into one direction and while doin a correction we se double top or bottom (where the distance between those swings need to be visible, no candle next to candle)
    we use this behavior as CONTINUATION of movement. after the second "touch" we are looking for "dynamic" (3+ single color candles) reaction of the price. it works the best on the tick or range chart.
    It is important that the wicks of double bottom or top do not allign perfectly we need to find a "center" of it


