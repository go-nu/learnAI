import { NextRequest, NextResponse } from 'next/server';

const BADGE_STYLES: Record<string, { color: string; badgeColor: string }> = {
  '긍정': { color: 'bg-emerald-50 border-emerald-200', badgeColor: 'bg-emerald-100 text-emerald-700' },
  '추천': { color: 'bg-blue-50 border-blue-200',       badgeColor: 'bg-blue-100 text-blue-700' },
  '제안': { color: 'bg-violet-50 border-violet-200',   badgeColor: 'bg-violet-100 text-violet-700' },
  '주의': { color: 'bg-amber-50 border-amber-200',     badgeColor: 'bg-amber-100 text-amber-700' },
  '부정': { color: 'bg-red-50 border-red-200',         badgeColor: 'bg-red-100 text-red-700' },
  '중립': { color: 'bg-gray-50 border-gray-200',       badgeColor: 'bg-gray-100 text-gray-600' },
};

// 이모지를 코드에서 고정 — 프롬프트에 넣으면 Gemini JSON 파싱 오류 발생
const INSIGHT_TEMPLATES = [
  { icon: '📈', label: '성장 트렌드' },        // 📈
  { icon: '🕐', label: '최적 업로드 패턴' }, // 🕐
  { icon: '🎯', label: '콘텐츠 전략 제안' }, // 🎯
  { icon: '⚠️', label: '이상값 · 주의 사항' }, // ⚠️
];

const DJANGO_BASE = 'http://127.0.0.1:8000/api/v1';
const GEMINI_MODEL = 'gemini-2.5-flash';

type EdaKpi = { channel_count: number; total_videos: number; total_views: number; avg_views: number };
type Trend  = { labels: string[]; data: number[] };
type ShortsRatio = { regular: number; shorts: number };
type EngSummary  = { avg_likes: number; avg_comments: number; like_rate: number };
type Top10Item   = { title: string; views: number; likes: number; is_short: boolean; duration: string };
type EdaPayload  = {
  kpi: EdaKpi;
  upload_trend: Trend;
  views_dist: Trend;
  shorts_ratio: ShortsRatio;
  weekday: Trend;
  top10: Top10Item[];
  engagement_summary: EngSummary;
};

type GeminiPart = { text?: string; thought?: boolean };
type GeminiResponse = {
  candidates?: { content?: { parts?: GeminiPart[] } }[];
  error?: { message?: string; status?: string };
};

function buildPrompt(eda: EdaPayload): string {
  const { kpi, upload_trend, views_dist, shorts_ratio, weekday, top10, engagement_summary } = eda;

  const maxUpload = Math.max(...upload_trend.data);
  const peakMonth = upload_trend.labels[upload_trend.data.indexOf(maxUpload)];

  const maxWeekday = Math.max(...weekday.data);
  const bestDay = weekday.labels[weekday.data.indexOf(maxWeekday)];

  const shortsTotal = shorts_ratio.regular + shorts_ratio.shorts;
  const shortsPct = shortsTotal > 0 ? Math.round((shorts_ratio.shorts / shortsTotal) * 100) : 0;

  const dataSummary = [
    `채널 수: ${kpi.channel_count}개`,
    `총 영상 수: ${kpi.total_videos.toLocaleString()}개`,
    `총 조회수: ${kpi.total_views.toLocaleString()}회`,
    `평균 조회수: ${kpi.avg_views.toLocaleString()}회`,
    '',
    '월별 업로드 추이:',
    ...upload_trend.labels.map((l, i) => `  ${l}: ${upload_trend.data[i]}개`),
    `  -> 최다 업로드 월: ${peakMonth} (${maxUpload}개)`,
    '',
    '조회수 구간별 분포:',
    ...views_dist.labels.map((l, i) => `  ${l}: ${views_dist.data[i]}개`),
    '',
    `콘텐츠 유형: 일반 ${shorts_ratio.regular}개 / Shorts ${shorts_ratio.shorts}개 (${shortsPct}%)`,
    '',
    '요일별 업로드:',
    ...weekday.labels.map((l, i) => `  ${l}: ${weekday.data[i]}개`),
    `  -> 최다 요일: ${bestDay} (${maxWeekday}개)`,
    '',
    `참여도: 평균 좋아요 ${engagement_summary.avg_likes.toLocaleString()} / 댓글 ${engagement_summary.avg_comments.toLocaleString()} / 좋아요율 ${engagement_summary.like_rate}%`,
    '',
    'TOP 3 영상:',
    ...top10.slice(0, 3).map((v, i) =>
      `  ${i + 1}. "${v.title}" - 조회수 ${v.views.toLocaleString()}, 좋아요 ${v.likes.toLocaleString()}, ${v.is_short ? 'Shorts' : '일반'} (${v.duration})`
    ),
  ].join('\n');

  // 이모지는 프롬프트에서 제거 — 코드에서 INSIGHT_TEMPLATES로 고정 매핑
  return `당신은 YouTube 채널 데이터 분석 전문가입니다. 아래 EDA 데이터를 분석하여 JSON만 출력해주세요.

${dataSummary}

반드시 아래 JSON 구조만 반환하세요 (설명 텍스트, 마크다운 코드블록 없이 JSON만):
{
  "summary": "3~4문장 종합 요약 (핵심 수치 포함, 한국어)",
  "insights": [
    {
      "label": "성장 트렌드",
      "badge": "긍정 또는 부정 또는 중립 중 정확히 하나",
      "points": ["데이터 기반 인사이트 1", "인사이트 2", "인사이트 3"]
    },
    {
      "label": "최적 업로드 패턴",
      "badge": "추천",
      "points": ["요일/시간 패턴 인사이트 1", "인사이트 2", "인사이트 3"]
    },
    {
      "label": "콘텐츠 전략 제안",
      "badge": "제안",
      "points": ["전략 제안 1", "제안 2", "제안 3"]
    },
    {
      "label": "이상값 및 주의 사항",
      "badge": "주의",
      "points": ["주의 사항 1", "주의 사항 2", "주의 사항 3"]
    }
  ]
}`;
}

async function saveReportToDjango(
  channelId: string,
  summary: string,
  insights: unknown[],
): Promise<void> {
  try {
    await fetch(`${DJANGO_BASE}/ai-report/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel_id: channelId, summary, insights }),
    });
  } catch {
    // 저장 실패해도 AI 응답은 그대로 반환
  }
}

export async function POST(request: NextRequest) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { success: false, error: 'GEMINI_API_KEY가 서버에 설정되지 않았습니다. .env.local을 확인하세요.' },
      { status: 500 }
    );
  }

  let edaData: EdaPayload;
  let channelId = '';
  try {
    const body = await request.json();
    if (!body.edaData) throw new Error('missing edaData');
    edaData   = body.edaData as EdaPayload;
    channelId = (body.channel_id as string) ?? '';
  } catch {
    return NextResponse.json({ success: false, error: 'EDA 데이터가 없습니다.' }, { status: 400 });
  }

  const prompt = buildPrompt(edaData);
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${apiKey}`;

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.4,
          maxOutputTokens: 2048,
          responseMimeType: 'application/json',  // JSON 모드: 마크다운/이모지 파싱 오류 방지
        },
      }),
    });

    const geminiData = await res.json() as GeminiResponse;

    if (!res.ok) {
      return NextResponse.json(
        { success: false, error: `Gemini API 오류: ${geminiData.error?.message ?? res.statusText}` },
        { status: 502 }
      );
    }

    // gemini-2.5-flash는 parts 배열에 thinking 토큰(thought:true)을 먼저 넣고
    // 실제 응답을 마지막 part에 넣음 → thought가 없는 마지막 part를 사용
    const parts = geminiData.candidates?.[0]?.content?.parts ?? [];
    const actualPart = [...parts].reverse().find(p => !p.thought) ?? parts[parts.length - 1];
    const rawText = (actualPart?.text ?? '').trim();
    if (!rawText) {
      return NextResponse.json({ success: false, error: 'Gemini 응답이 비어 있습니다.' }, { status: 500 });
    }

    // JSON 모드에서는 rawText가 곧 JSON이지만, 안전을 위해 중괄호 범위도 추출
    let jsonStr = rawText;
    const jsonMatch = rawText.match(/\{[\s\S]*\}/);
    if (jsonMatch) jsonStr = jsonMatch[0];

    let parsed: {
      summary: string;
      insights: { label: string; badge: string; points: string[] }[];
    };
    try {
      parsed = JSON.parse(jsonStr);
    } catch (parseErr: unknown) {
      const msg = parseErr instanceof Error ? parseErr.message : String(parseErr);
      return NextResponse.json(
        { success: false, error: `AI 응답 JSON 파싱 실패: ${msg}` },
        { status: 500 }
      );
    }

    // 이모지(icon)와 라벨은 INSIGHT_TEMPLATES에서 고정 매핑
    const insights = INSIGHT_TEMPLATES.map((tmpl, i) => {
      const src = parsed.insights?.[i] ?? { badge: '중립', points: [] };
      const badge = src.badge ?? '중립';
      return {
        icon:  tmpl.icon,
        label: tmpl.label,
        badge,
        points: src.points ?? [],
        ...(BADGE_STYLES[badge] ?? BADGE_STYLES['중립']),
      };
    });

    if (channelId && channelId !== 'all') {
      await saveReportToDjango(channelId, parsed.summary, insights);
    }

    return NextResponse.json({ success: true, summary: parsed.summary, insights });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'AI 분석 중 오류가 발생했습니다.';
    return NextResponse.json({ success: false, error: msg }, { status: 500 });
  }
}
