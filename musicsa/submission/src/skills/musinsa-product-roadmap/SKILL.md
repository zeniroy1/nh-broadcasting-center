---
name: musinsa-product-roadmap
description: Use this skill when designing, reviewing, running, or extending the Musinsa public-signal product search and comparison prototype that converts user purchase intent into explainable product candidates.
---

# Musinsa Product Search

## Purpose

Help operate and extend a product search and parsing assistant for Musinsa that reduces the effort required for a shopper to reach suitable products.

The assistant should not claim access to Musinsa internal data. It should use only public signals and clearly label inferred metrics as estimates.

## Core Workflow

1. Interpret the user's natural-language purchase request.
2. Convert the request into structured shopping conditions.
3. Generate multiple search keyword candidates.
4. Gather public signals from search, ranking, category, and product-detail pages.
5. Map unavailable internal metrics to public proxy metrics.
6. Score products with explainable criteria.
7. Deduplicate brands and products.
8. Produce a short comparison table.
9. Explain why each candidate is recommended.
10. Show cautions and uncertainty clearly.

## Public Signals

Use signals such as:

- Product name
- Brand
- Category
- Price
- Original price
- Discount rate
- Review count
- Review score
- Sales label
- Viewing-now label
- Buying-now label
- Search result position
- Ranking position
- Gender-filtered ranking position
- Age-filtered ranking position when visible
- Delivery information
- Sold-out status
- Size and option availability
- Product images and descriptions
- Review keywords

## Proxy Metric Rules

Do not state internal metrics as facts.

Instead map them as follows:

| Desired internal metric | Public proxy metric |
|---|---|
| Actual cumulative buyers | Sales label, review count, ranking exposure |
| 40s male buyers | Male/40s ranking exposure, male ranking exposure |
| Gender conversion rate | Male/female ranking comparison |
| Cart conversion rate | Buying-now, viewing-now, review volume |
| Return rate | Low-rating review keywords and fit complaints |
| Repurchase rate | Review keywords such as repurchase or bought again |
| Advertising influence | AD/sponsored/campaign exposure marker |
| Search exposure score | Search result position by keyword and sort mode |

## Recommended Scoring Dimensions

- Purpose fit score
- Popularity proxy score
- Trust score
- Male fit score
- Age fit proxy score
- Price fit score
- Delivery score
- Review risk score
- Final score

## Required Wording Discipline

Bad:

```text
40대 남성이 가장 많이 산 상품입니다.
```

Good:

```text
남성/40대 조건의 랭킹 노출, 리뷰 수, 평점, 판매 라벨을 기준으로 40대 남성에게 적합할 가능성이 높은 상품입니다.
```

Bad:

```text
반품률이 낮은 상품입니다.
```

Good:

```text
낮은 평점 리뷰에서 사이즈/품질 불만 키워드가 적어 반품 리스크가 낮을 가능성이 있습니다.
```

## Prototype Scope

The current prototype includes:

```text
무신사 공개 지표 기반 제품 검색·비교 도우미
```

Implemented capabilities:

- Natural-language condition parsing
- Public Musinsa HTML/JSON collection where available
- Product, color, price, brand, and target-fit filtering
- Five-candidate comparison output
- Three-candidate shortlist detail view
- Buyer-facing local HTML UI
- Standalone Windows EXE build configuration

Still excluded:

- Login-based personalization
- Claims about exact buyer count
- High-frequency crawling
- Claims about internal Musinsa ranking, conversion, return, or repurchase data

## Output Format

Prefer this structure:

```text
1. Product candidate
- Brand:
- Product:
- Price:
- Public evidence:
- Estimated fit:
- Recommendation reason:
- Caution:
- Product URL:
```

Always separate confirmed public facts from inferred proxy scores.
