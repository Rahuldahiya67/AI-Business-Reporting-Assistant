-- Business Reporting Assistant — SQL Views

CREATE VIEW IF NOT EXISTS v_summary AS
SELECT
    COUNT(DISTINCT campaign_id)                                    AS total_campaigns,
    ROUND(SUM(spend), 2)                                           AS total_spend,
    ROUND(SUM(revenue), 2)                                         AS total_revenue,
    ROUND(SUM(revenue) - SUM(spend), 2)                            AS total_profit,
    SUM(clicks)                                                    AS total_clicks,
    SUM(impressions)                                               AS total_impressions,
    SUM(conversions)                                               AS total_conversions,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS overall_roas,
    ROUND(SUM(spend)   / NULLIF(SUM(clicks), 0), 3)                AS avg_cpc,
    ROUND(SUM(spend)   / NULLIF(SUM(impressions), 0) * 1000, 3)    AS avg_cpm,
    ROUND(SUM(spend)   / NULLIF(SUM(conversions), 0), 3)           AS avg_cpa
FROM campaigns;

CREATE VIEW IF NOT EXISTS v_by_channel AS
SELECT channel,
    COUNT(*)                                                       AS num_campaigns,
    ROUND(SUM(spend), 2)                                           AS spend,
    ROUND(SUM(revenue), 2)                                         AS revenue,
    ROUND(SUM(revenue) - SUM(spend), 2)                            AS profit,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS roas,
    ROUND(SUM(spend)   / NULLIF(SUM(clicks), 0), 3)                AS cpc,
    ROUND(SUM(spend)   / NULLIF(SUM(impressions), 0) * 1000, 3)    AS cpm,
    ROUND(SUM(spend)   / NULLIF(SUM(conversions), 0), 3)           AS cpa
FROM campaigns GROUP BY channel ORDER BY roas DESC;

CREATE VIEW IF NOT EXISTS v_by_product AS
SELECT product,
    ROUND(SUM(spend), 2)                                           AS spend,
    ROUND(SUM(revenue), 2)                                         AS revenue,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS roas,
    ROUND(SUM(spend)   / NULLIF(SUM(conversions), 0), 3)           AS cpa,
    SUM(conversions)                                               AS conversions
FROM campaigns GROUP BY product ORDER BY revenue DESC;

CREATE VIEW IF NOT EXISTS v_by_region AS
SELECT region,
    ROUND(SUM(spend), 2)                                           AS spend,
    ROUND(SUM(revenue), 2)                                         AS revenue,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS roas
FROM campaigns GROUP BY region ORDER BY revenue DESC;

CREATE VIEW IF NOT EXISTS v_monthly_trend AS
SELECT STRFTIME('%Y-%m', campaign_date)                            AS month,
    ROUND(SUM(spend), 2)                                           AS spend,
    ROUND(SUM(revenue), 2)                                         AS revenue,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS roas,
    SUM(conversions)                                               AS conversions
FROM campaigns GROUP BY month ORDER BY month;

CREATE VIEW IF NOT EXISTS v_top_roas AS
SELECT campaign_id, channel, product, region,
    ROUND(spend, 2)                                                AS spend,
    ROUND(revenue, 2)                                              AS revenue,
    ROUND(revenue / NULLIF(spend, 0), 3)                           AS roas,
    ROUND(spend   / NULLIF(conversions, 0), 3)                     AS cpa,
    conversions
FROM campaigns ORDER BY roas DESC LIMIT 10;

CREATE VIEW IF NOT EXISTS v_underperformers AS
SELECT campaign_id, channel, product,
    ROUND(spend, 2)                                                AS spend,
    ROUND(revenue / NULLIF(spend, 0), 3)                           AS roas,
    ROUND(revenue - spend, 2)                                      AS profit_loss
FROM campaigns WHERE (revenue / NULLIF(spend, 0)) < 1.5
ORDER BY profit_loss ASC;
