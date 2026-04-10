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
    If the body of the candles close/open in the same "area" then the wicks does not really matter
    Double bottom or top also shows that correction may end and the trend starts 
    
OHLC
    D1
    we take open, high, low, close values

    if current price is in the candle body zone it is "maybe" zone
    for bearish D1 candle
    if current price is in the open and end of the wick then we are in the "promotion for sellers zone"
    if current price is in the close and end of the wick area then we are in the "promotion for buyers zone"
    for bullis is vice versa

SESSION OBJECTIVE
    Polish TIME
    ASIA 23:00 - 7:59
    LONDON 09:00 - 13:00
    AMERICA 14:00 - 21:00 

    After creation of the box(high and low values) we have 2 zones, one above and one below. Those are promo zones for EU. so either people will want to take profits in those areas or open a trade
    It works the same for the LONDON box. Outside of it we see a US promo zone.

MEASURED-MOVE
    Signal/gap candles are not important here
    AB - Impulse begins on one side of EMA and clearly ends on the opposite side (we do not count cases when the wicks/candles are "touching" the EMA, we need a clear opposite movement)
    BC (pullback) - point C must be clearly on the same side as point A
    Measured-move(D) - in a trend used to define the target for the current momentum
    AB=CD
    we use fibo expansion to draw it on chart
    mark ABC to get D
    here we need to have in mind all of previous steps like fibo levels and so on
    the movement needs to be "clean"
    If price after moving from C reaches B level and makes deeper correction then C level it means that our measured move it pointless. it is basically rest of measured move

    for furutre strategy plans
    3rd leg is measured from deepest correction after measured move and touches the ema so we see it as sort of valid setup but usually it bouces from some cluster or so

    DOUBLE UP & DOUBLE DOWN
        AB - impulse begins on the the one side of EMA and clearly ends on the opposite side
        another view of Measured-move
        we use fibo retracement to draw it
        triple down is a S/R line

    Combination of both mesured-move and double up and double down can work together very well to create a support area
    the 3rd leg of measured move can allign with double up and double down value

Hidden Channel - rotation channel (2 paralalel lines)
    Price hit the target or some important level, measured-move, double top or double bottom
    There is a reaction and move with new momentum. There should be an impulse.
    Grab Channel to know where is the best spot to follow the new momentum
    lack of rotation
    we look for clean impulse so we can create the channel.
    there's a chance of "false retest" which means that only one side of channel is tested. In such cases we should wait.
    so at the beginning of this rotation we can go with measured move
    and with signal candle within correct context (bearish below ema or strongly crossing it vice versa for bullish)
    the settlement of trade should be done few pips before the target

BATTLE ZONE
    S/R zones based on swings
    Resistance - the range where the sellers/buyers (the oposite direction traders) gained an advantage
    Support - vice versa from resistance
    Untested - swing on which a strong reaction appeared, range, not re-tested
    verified - zone which was retested by price at least once
    turncoat - zone with a possible change of character from support to resistance or vice versa
    Battlezone - where swings are very close to each other, buyers win and sellers win etc. we mark it from the highest to lowest swing
    if the battle zone is crossed in oposite direction (so the market trend was bearish but buyers crossed it) the battle zone is void. we may look an opportunity to open a BUY trade.

    With each re-test zone becomes weaker

SPIKE & MOVE (Spike & channel)
    Spike - sudden change in price over a short period of time (it does not need to be one candle it can be even 10 if it is sudden change in price)
    Wait for pullback to 50% FIBB of Spike AB
        A - open of spike
        B - highest level of channel/move
        C - 50% FIBB of Spike AB (price need to react on it but if it cross it then whole spike & move setup is burned)
        D - measured move from ABC