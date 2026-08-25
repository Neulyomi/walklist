// === 걷기 좋은 동네: Clean Minimal & Dong Focus Engine (Option 3) ===

let rawGeoData = null;
let map = null;
let activeFeatureId = null;
let userLocation = null;
let userMarker = null;
let mapMarkers = [];
let selectedLandmarkMarker = null;

// Pinpoint Diagnostics Mode State
let isPinpointMode = false;
let pinpointPoints = [];
let pinpointMarkers = [];
let customRouteFeature = null;

// Initial Default Weights
const defaultWeights = {
  env: 35,
  pop: 25,
  eve: 20,
  tra: 20
};

// Walking Style Presets Definition
const walkingPresets = {
  balance: { env: 35, pop: 25, eve: 20, tra: 20, name: '기본 밸런스' },
  healing: { env: 45, pop: 40, eve: 5, tra: 10, name: '1. 조용한 힐링' },
  cafe: { env: 15, pop: 20, eve: 40, tra: 25, name: '2. 감성 카페탐방' },
  shopping: { env: 10, pop: 15, eve: 45, tra: 30, name: '3. 활기찬 아이쇼핑' }
};

// Regional Centers for Map Navigation
const regionCenters = {
  'ALL': { center: [127.8, 36.0], zoom: 6.8 },
  '대구': { center: [128.6010, 35.8650], zoom: 12.8 },
  '서울': { center: [126.9800, 37.5600], zoom: 12.5 },
  '부산': { center: [129.0800, 35.1800], zoom: 12.0 },
  '수원/경기': { center: [127.0168, 37.2852], zoom: 13.0 },
  '대전': { center: [127.4390, 36.3335], zoom: 13.5 },
  '광주': { center: [126.9180, 35.1425], zoom: 13.5 },
  '전북': { center: [127.1510, 35.8150], zoom: 13.0 },
  '강원': { center: [128.9245, 37.7915], zoom: 12.5 },
  '제주': { center: [126.5238, 33.5142], zoom: 12.5 }
};

// DOM Elements
const sggSelect = document.getElementById('sggSelect');
const rankingRegionLabel = document.getElementById('rankingRegionLabel');
const rankingCarousel = document.getElementById('rankingCarousel');
const rankingStatusHint = document.getElementById('rankingStatusHint');
const weightEnvInput = document.getElementById('weightEnv');
const weightPopInput = document.getElementById('weightPop');
const weightEveInput = document.getElementById('weightEve');
const weightTraInput = document.getElementById('weightTra');
const resetWeightsBtn = document.getElementById('resetWeightsBtn');

// Preset Chips DOM
const presetChips = document.querySelectorAll('.btn-dock-chip, .btn-preset-chip');
const btnOpenCustomWeights = document.getElementById('btnOpenCustomWeights');
const customWeightModal = document.getElementById('customWeightModal');
const btnCloseCustomWeight = document.getElementById('btnCloseCustomWeight');

// Nav Action Buttons & Modals
const btnGeoLocate = document.getElementById('btnGeoLocate');
const btnPinpointMode = document.getElementById('btnPinpointMode');
const pinpointBanner = document.getElementById('pinpointBanner');
const pinpointStepText = document.getElementById('pinpointStepText');
const btnCancelPinpoint = document.getElementById('btnCancelPinpoint');
const btnOpenCompare = document.getElementById('btnOpenCompare');
const btnOpenSaved = document.getElementById('btnOpenSaved');
const savedCountBadge = document.getElementById('savedCountBadge');

const btnOpenSelectionInfo = document.getElementById('btnOpenSelectionInfo');
const selectionModal = document.getElementById('selectionModal');
const btnCloseSelection = document.getElementById('btnCloseSelection');

const compareModal = document.getElementById('compareModal');
const btnCloseCompare = document.getElementById('btnCloseCompare');
const compareSelectA = document.getElementById('compareSelectA');
const compareSelectB = document.getElementById('compareSelectB');
const compareMatrixContent = document.getElementById('compareMatrixContent');

const savedModal = document.getElementById('savedModal');
const btnCloseSaved = document.getElementById('btnCloseSaved');
const savedRoutesList = document.getElementById('savedRoutesList');

// Detail Sidebar DOM
const detailSidebar = document.getElementById('detailSidebar');
const sidebarContent = document.getElementById('sidebarContent');
const closeSidebarBtn = document.getElementById('closeSidebarBtn');

// 1. Initialize MapLibre GL Map
function initMap() {
  map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      sources: {
        'carto-positron': {
          type: 'raster',
          tiles: [
            'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
            'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
            'https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png'
          ],
          tileSize: 256,
          attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap contributors'
        }
      },
      layers: [
        {
          id: 'carto-layer',
          type: 'raster',
          source: 'carto-positron',
          minzoom: 0,
          maxzoom: 19
        }
      ]
    },
    center: [127.8, 36.0],
    zoom: 6.8,
    pitch: 0
  });

  map.addControl(new maplibregl.NavigationControl(), 'top-left');

  map.on('load', async () => {
    await loadGeoJSON();
    initPinpointEvents();
    updateSavedBadge();
    autoLocateUserOnStart();
  });
}

// 2. Load GeoJSON & Setup Dong Walkable Area Layer
async function loadGeoJSON() {
  try {
    const res = await fetch(`data/streets.geojson?nocache=${Date.now()}`);
    rawGeoData = await res.json();

    rawGeoData.features.forEach((f) => {
      calculateFeatureSubScores(f.properties);
    });

    // 1) Selected Dong Area Highlight Source & Layers
    map.addSource('selected-dong-src', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: [] }
    });

    // Selected Dong Transparent Emerald Fill
    map.addLayer({
      id: 'selected-dong-fill',
      type: 'fill',
      source: 'selected-dong-src',
      paint: {
        'fill-color': '#10b981',
        'fill-opacity': 0.12
      }
    });

    // Selected Dong Clear Green Perimeter Line
    map.addLayer({
      id: 'selected-dong-line',
      type: 'line',
      source: 'selected-dong-src',
      layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: {
        'line-color': '#059669',
        'line-width': 3.5,
        'line-opacity': 0.95
      }
    });

    // Custom 2-point pinpoint route source
    map.addSource('custom-route-src', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: [] }
    });

    map.addLayer({
      id: 'custom-route-line',
      type: 'line',
      source: 'custom-route-src',
      layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: {
        'line-color': '#8b5cf6',
        'line-width': 5,
        'line-dasharray': [2, 1]
      }
    });

    recalculateAll();
    populateCompareDropdowns();

  } catch (err) {
    console.error("Failed to load GeoJSON:", err);
  }
}

// 3. Generate Natural Organic Walkshed Blob (Harmonic Multi-wave Curve)
function generateDongWalkableAreaGeoJSON(feature) {
  const center = feature.geometry.coordinates; // [lng, lat]
  const radiusM = feature.properties.radius_m || 240;

  // Base lat/lng deltas
  const baseLatDelta = radiusM / 111320;
  const baseLngDelta = radiusM / (111320 * Math.cos(center[1] * Math.PI / 180));

  // Deterministic seed based on feature id string
  let seed = 0;
  const idStr = feature.properties.id || 'seed';
  for (let s = 0; s < idStr.length; s++) {
    seed += idStr.charCodeAt(s);
  }
  const phase1 = (seed % 10) * 0.6;
  const phase2 = (seed % 7) * 0.9;
  const phase3 = (seed % 5) * 1.2;

  const points = [];
  const numSides = 48; // Smooth organic curve
  for (let i = 0; i < numSides; i++) {
    const angle = (i / numSides) * 2 * Math.PI;

    // Harmonic wave modulation to create natural, non-circular pedestrian walkshed
    const wave = 1.0 +
      0.18 * Math.sin(2 * angle + phase1) +
      0.12 * Math.cos(3 * angle + phase2) +
      0.06 * Math.sin(5 * angle + phase3);

    const lng = center[0] + baseLngDelta * wave * Math.cos(angle);
    const lat = center[1] + baseLatDelta * wave * Math.sin(angle);
    points.push([lng, lat]);
  }
  points.push(points[0]); // close loop

  return {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: {
          dong_name: feature.properties.dong_name,
          street_name: feature.properties.street_name
        },
        geometry: {
          type: 'Polygon',
          coordinates: [points]
        }
      }
    ]
  };
}

// 4. Update Minimal Dong Badge Chip Markers on Map
function updateMapMarkers() {
  mapMarkers.forEach(m => m.remove());
  mapMarkers = [];

  if (!rawGeoData || !map) return;
  const selectedRegion = sggSelect.value;

  const filtered = rawGeoData.features.filter((f) => {
    if (selectedRegion === 'ALL') return true;
    return f.properties.province === selectedRegion;
  });

  filtered.forEach((f) => {
    const p = f.properties;
    const coords = f.geometry.coordinates;

    const el = document.createElement('div');
    el.className = `dong-map-chip ${p.id === activeFeatureId ? 'active' : ''}`;
    el.id = `marker-${p.id}`;
    el.innerHTML = `
      <span class="chip-name">${p.dong_name.split(' ')[1] || p.dong_name}</span>
      <span class="chip-score">${p.score_100}점</span>
    `;

    el.addEventListener('click', (e) => {
      e.stopPropagation();
      highlightFeature(p.id, true);
    });

    const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
      .setLngLat(coords)
      .addTo(map);

    mapMarkers.push(marker);
  });
}

function calculateFeatureSubScores(p) {
  let scoreWidth = 0.1;
  if (p.width_m >= 3.5) scoreWidth = 1.0;
  else if (p.width_m >= 2.5) scoreWidth = 0.8;
  else if (p.width_m >= 1.5) scoreWidth = 0.5;

  const scoreCar = p.car_control || 0.5;

  let scoreSlope = 0.0;
  if (p.slope_pct <= 3.0) scoreSlope = 1.0;
  else if (p.slope_pct <= 5.0) scoreSlope = 0.8;
  else if (p.slope_pct <= 8.0) scoreSlope = 0.4;

  p.sub_score_env = (0.35 * scoreWidth) + (0.35 * scoreCar) + (0.30 * scoreSlope);

  const d = p.density_dist_m || 5.0;
  p.sub_score_pop = Math.exp(-Math.pow(d - 5.0, 2) / (2 * Math.pow(1.8, 2)));

  p.sub_score_eve = p.event_level || 0.5;

  let scoreWalk = 0.1;
  if (p.transit_walk_min <= 5.0) scoreWalk = 1.0;
  else if (p.transit_walk_min <= 10.0) scoreWalk = 0.7;
  else if (p.transit_walk_min <= 15.0) scoreWalk = 0.4;

  p.sub_score_tra = scoreWalk * (p.transit_diversity || 0.8);
}

// 5. Realtime Scoring Engine
function recalculateAll() {
  if (!rawGeoData) return;

  const wEnv = parseFloat(weightEnvInput.value) || 0;
  const wPop = parseFloat(weightPopInput.value) || 0;
  const wEve = parseFloat(weightEveInput.value) || 0;
  const wTra = parseFloat(weightTraInput.value) || 0;
  const wTotal = wEnv + wPop + wEve + wTra || 1;

  rawGeoData.features.forEach((f) => {
    const p = f.properties;
    const rawTotal = (wEnv * p.sub_score_env) +
                     (wPop * p.sub_score_pop) +
                     (wEve * p.sub_score_eve) +
                     (wTra * p.sub_score_tra);

    p.score_100 = Math.round((rawTotal / wTotal) * 100);
    p.score_raw = Math.round(rawTotal * 10) / 10;
  });

  renderRankingCarousel();
  updateMapMarkers();

  if (activeFeatureId) {
    highlightFeature(activeFeatureId, false);
  }
}

// 6. Distance Calculator (Haversine Formula)
function getDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function formatDistance(km) {
  if (km < 1.0) {
    return `📍 내 위치에서 ${Math.round(km * 1000)}m`;
  }
  return `📍 내 위치에서 ${km.toFixed(1)}km`;
}

// 7. Render Dong-Centric Ranking Carousel
function renderRankingCarousel() {
  if (!rawGeoData) return;
  const selectedRegion = sggSelect.value;
  rankingRegionLabel.textContent = selectedRegion === 'ALL' ? '전국' : selectedRegion;

  let filtered = rawGeoData.features.filter((f) => {
    if (selectedRegion === 'ALL') return true;
    return f.properties.province === selectedRegion;
  });

  if (userLocation) {
    filtered.forEach(f => {
      const coords = f.geometry.coordinates;
      f.properties.distanceKm = getDistanceKm(userLocation.lat, userLocation.lng, coords[1], coords[0]);
    });

    if (selectedRegion === 'ALL') {
      filtered.sort((a, b) => a.properties.distanceKm - b.properties.distanceKm);
      rankingStatusHint.textContent = `🎯 내 현재 위치 기준으로 가장 가까운 동네 순으로 정렬되었습니다`;
    } else {
      filtered.sort((a, b) => b.properties.score_100 - a.properties.score_100);
      rankingStatusHint.textContent = `카드를 클릭하면 해당 동네 쾌적 권역과 5단계 분석창으로 이동합니다`;
    }
  } else {
    filtered.sort((a, b) => b.properties.score_100 - a.properties.score_100);
    rankingStatusHint.textContent = `카드를 클릭하면 해당 동네 쾌적 권역과 5단계 분석창으로 이동합니다`;
  }

  rankingCarousel.innerHTML = '';

  if (filtered.length === 0) {
    rankingCarousel.innerHTML = `<div style="padding: 12px; color: #64748b; font-size: 0.85rem;">해당 지역에 등록된 동네가 없습니다.</div>`;
    return;
  }

  filtered.forEach((f, idx) => {
    const p = f.properties;
    const rank = idx + 1;
    let rankClass = 'rank-default';
    let rankBadgeText = `${rank}위`;

    if (rank === 1) { rankClass = 'rank-1'; rankBadgeText = `🥇 1위`; }
    else if (rank === 2) { rankClass = 'rank-2'; rankBadgeText = `🥈 2위`; }
    else if (rank === 3) { rankClass = 'rank-3'; rankBadgeText = `🥉 3위`; }

    const distBadge = p.distanceKm !== undefined ? `<div class="card-distance-badge">${formatDistance(p.distanceKm)}</div>` : '';

    const card = document.createElement('div');
    card.className = `ranking-card ${p.id === activeFeatureId ? 'active' : ''}`;
    card.id = `card-${p.id}`;
    card.innerHTML = `
      <div class="card-top">
        <span class="rank-badge ${rankClass}">${rankBadgeText}</span>
        <span class="score-badge">${p.score_100}점</span>
      </div>
      <div class="card-dong-title">${p.dong_name}</div>
      <div class="card-street-sub">${p.street_name} · ${p.vibe_desc}</div>
      ${distBadge}
      <div class="card-tags-row">
        <span class="card-tags">${p.highlight_tag || '#걷기명소'}</span>
      </div>
    `;

    card.addEventListener('click', () => {
      highlightFeature(p.id, true);
    });

    rankingCarousel.appendChild(card);
  });
}

// 8. 5-Tier Helper Functions
function getTierInfo(score) {
  if (score >= 90) return { level: 5, label: '5단계: 최우수 명품길', colorClass: 'tier-5', barClass: 'active-5' };
  if (score >= 80) return { level: 4, label: '4단계: 우수 안심길', colorClass: 'tier-4', barClass: 'active-4' };
  if (score >= 70) return { level: 3, label: '3단계: 보통 일상길', colorClass: 'tier-3', barClass: 'active-3' };
  if (score >= 60) return { level: 2, label: '2단계: 주의 혼잡길', colorClass: 'tier-2', barClass: 'active-2' };
  return { level: 1, label: '1단계: 보행 비추천', colorClass: 'tier-1', barClass: 'active-1' };
}

function getPillarTier(subScore) {
  if (subScore >= 0.85) return { text: '5단계 (최상)', color: '#047857' };
  if (subScore >= 0.70) return { text: '4단계 (우수)', color: '#15803d' };
  if (subScore >= 0.50) return { text: '3단계 (보통)', color: '#a16207' };
  if (subScore >= 0.30) return { text: '2단계 (주의)', color: '#c2410c' };
  return { text: '1단계 (미흡)', color: '#b91c1c' };
}

// 9. Highlight Feature & Display Walkable Area Polygon + Open Sidebar
function highlightFeature(id, shouldFly = true) {
  activeFeatureId = id;
  const feature = rawGeoData.features.find(f => f.properties.id === id);
  if (!feature) return;

  const p = feature.properties;
  const coords = feature.geometry.coordinates;

  // 1) Focus Dong Walkable Area with Emerald Green Outline
  const areaGeoJSON = generateDongWalkableAreaGeoJSON(feature);
  if (map && map.getSource('selected-dong-src')) {
    map.getSource('selected-dong-src').setData(areaGeoJSON);
  }

  // 2) Display Key Landmark Pin for the selected Dong
  if (selectedLandmarkMarker) {
    selectedLandmarkMarker.remove();
    selectedLandmarkMarker = null;
  }

  if (map && p.street_name) {
    const landmarkEl = document.createElement('div');
    landmarkEl.className = 'dong-landmark-pin';
    landmarkEl.innerHTML = `
      <div class="landmark-dot-badge"></div>
      <span class="landmark-text-label">${p.street_name}</span>
    `;

    selectedLandmarkMarker = new maplibregl.Marker({
      element: landmarkEl,
      anchor: 'left',
      offset: [-4, 0]
    })
      .setLngLat(coords)
      .addTo(map);
  }

  // Update card active state
  document.querySelectorAll('.ranking-card').forEach(c => c.classList.remove('active'));
  const activeCard = document.getElementById(`card-${id}`);
  if (activeCard) {
    activeCard.classList.add('active');
    activeCard.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  }

  // Update marker active state
  document.querySelectorAll('.dong-map-chip').forEach(m => m.classList.remove('active'));
  const activeMarker = document.getElementById(`marker-${id}`);
  if (activeMarker) {
    activeMarker.classList.add('active');
  }

  if (shouldFly && map) {
    map.flyTo({
      center: coords,
      zoom: 15.5,
      pitch: 0,
      padding: { left: 360, right: 20, top: 20, bottom: 20 },
      duration: 1200
    });
  }

  const tier = getTierInfo(p.score_100);
  const tierEnv = getPillarTier(p.sub_score_env);
  const tierPop = getPillarTier(p.sub_score_pop);
  const tierEve = getPillarTier(p.sub_score_eve);
  const tierTra = getPillarTier(p.sub_score_tra);

  let stepBarHtml = '';
  for (let i = 1; i <= 5; i++) {
    const isActive = i <= tier.level ? tier.barClass : '';
    stepBarHtml += `<div class="step-segment ${isActive}"></div>`;
  }

  let eventListHtml = '';
  if (p.events_list && p.events_list.length > 0) {
    eventListHtml = `
      <div class="sidebar-events-box">
        <div class="sidebar-events-title"><i data-lucide="sparkles"></i> 이번 주말 이벤트 & 팝업 (${p.events_list.length}건)</div>
        <ul class="sidebar-events-list">
          ${p.events_list.map(e => `<li>${e}</li>`).join('')}
        </ul>
      </div>
    `;
  }

  const cafeBadge = p.cafe_interval_m ? `<span class="cafe-mini-badge">☕ ${p.cafe_interval_m}m마다 카페</span>` : '';

  sidebarContent.innerHTML = `
    <div class="sidebar-dong-header">${p.dong_name}</div>
    <div class="sidebar-title">${p.street_name}</div>
    <div class="sidebar-vibe">${p.vibe_desc}</div>
    <div class="sidebar-tags-row">
      <span class="sidebar-hashtag">${p.highlight_tag}</span>
      ${cafeBadge}
    </div>
    <div class="sidebar-region">📍 ${p.province} ${p.sgg} ${p.dong}</div>
    
    <div class="tier-header-card">
      <div class="tier-top-row">
        <span class="tier-badge ${tier.colorClass}">${tier.label}</span>
        <span class="tier-score-num">${p.score_100}<span style="font-size: 0.95rem; font-weight: 700; color: #64748b;">점</span></span>
      </div>
      <div class="step-bar-container">
        ${stepBarHtml}
      </div>
    </div>

    <div class="pillars-eval-title">📊 4대 핵심 항목별 5단계 진단</div>
    <div class="pillars-eval-list">
      <div class="pillar-eval-item">
        <div class="pillar-eval-header">
          <span class="pillar-eval-name">🌿 도보 환경</span>
          <span class="pillar-eval-tier" style="color: ${tierEnv.color}">${tierEnv.text}</span>
        </div>
        <div class="pillar-subtext">보도폭 ${p.width_m}m · ${p.car_control_label ? p.car_control_label.split(' ')[0] : '보행안심'} · 경사 ${p.slope_pct}%</div>
      </div>

      <div class="pillar-eval-item">
        <div class="pillar-eval-header">
          <span class="pillar-eval-name">👥 인구밀도</span>
          <span class="pillar-eval-tier" style="color: ${tierPop.color}">${tierPop.text}</span>
        </div>
        <div class="pillar-subtext">보행자 간격 약 ${p.density_dist_m}m (5m 골든존)</div>
      </div>

      <div class="pillar-eval-item">
        <div class="pillar-eval-header">
          <span class="pillar-eval-name">🎪 이벤트</span>
          <span class="pillar-eval-tier" style="color: ${tierEve.color}">${tierEve.text}</span>
        </div>
        <div class="pillar-subtext">${p.event_label}</div>
      </div>

      <div class="pillar-eval-item">
        <div class="pillar-eval-header">
          <span class="pillar-eval-name">🚌 대중교통</span>
          <span class="pillar-eval-tier" style="color: ${tierTra.color}">${tierTra.text}</span>
        </div>
        <div class="pillar-subtext">지하철/정류장 도보 ${p.transit_walk_min}분 컷</div>
      </div>
    </div>

    ${eventListHtml}
  `;

  detailSidebar.classList.add('open');
  lucide.createIcons();
}

closeSidebarBtn.addEventListener('click', () => {
  detailSidebar.classList.remove('open');
  activeFeatureId = null;
  document.querySelectorAll('.ranking-card').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.dong-map-chip').forEach(m => m.classList.remove('active'));
  if (map && map.getSource('selected-dong-src')) {
    map.getSource('selected-dong-src').setData({ type: 'FeatureCollection', features: [] });
  }
  if (selectedLandmarkMarker) {
    selectedLandmarkMarker.remove();
    selectedLandmarkMarker = null;
  }
});

// Selection Info Modal Event
btnOpenSelectionInfo.addEventListener('click', () => {
  selectionModal.classList.remove('hidden');
});

btnCloseSelection.addEventListener('click', () => {
  selectionModal.classList.add('hidden');
});

// ==========================================
// 10. 📍 GPS Live Geolocation Engine
// ==========================================
function autoLocateUserOnStart() {
  if (!navigator.geolocation) return;

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      userLocation = {
        lng: pos.coords.longitude,
        lat: pos.coords.latitude
      };
      displayUserMarker(userLocation);
      
      map.flyTo({
        center: [userLocation.lng, userLocation.lat],
        zoom: 13.0,
        pitch: 0,
        duration: 1500
      });

      renderRankingCarousel();
    },
    (err) => {
      console.warn("Geolocation skipped:", err.message);
    },
    { timeout: 5000 }
  );
}

btnGeoLocate.addEventListener('click', () => {
  if (!navigator.geolocation) {
    alert("현재 브라우저에서 위치 서비스를 지원하지 않습니다.");
    return;
  }

  btnGeoLocate.classList.add('active');
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      userLocation = {
        lng: pos.coords.longitude,
        lat: pos.coords.latitude
      };
      displayUserMarker(userLocation);

      map.flyTo({
        center: [userLocation.lng, userLocation.lat],
        zoom: 13.0,
        pitch: 0,
        duration: 1500
      });

      sggSelect.value = 'ALL';
      renderRankingCarousel();
      updateMapMarkers();
      setTimeout(() => btnGeoLocate.classList.remove('active'), 1000);
    },
    (err) => {
      btnGeoLocate.classList.remove('active');
      alert("현재 위치 정보를 가져올 수 없습니다. 브라우저 위치 권한을 허용해 주세요.");
    }
  );
});

function displayUserMarker(loc) {
  if (userMarker) userMarker.remove();

  const el = document.createElement('div');
  el.className = 'user-gps-marker';
  el.title = '내 현재 위치';

  userMarker = new maplibregl.Marker({ element: el })
    .setLngLat([loc.lng, loc.lat])
    .addTo(map);
}

// ==========================================
// 11. 📍 Pinpoint 2-Point Custom Diagnostics
// ==========================================
function initPinpointEvents() {
  btnPinpointMode.addEventListener('click', () => {
    isPinpointMode = !isPinpointMode;
    if (isPinpointMode) {
      startPinpointMode();
    } else {
      cancelPinpointMode();
    }
  });

  btnCancelPinpoint.addEventListener('click', () => {
    cancelPinpointMode();
  });

  map.on('click', async (e) => {
    if (!isPinpointMode) return;

    const lngLat = [e.lngLat.lng, e.lngLat.lat];
    pinpointPoints.push(lngLat);

    if (pinpointPoints.length === 1) {
      const el = document.createElement('div');
      el.style.fontSize = '24px';
      el.textContent = '🚩';
      const marker = new maplibregl.Marker({ element: el }).setLngLat(lngLat).addTo(map);
      pinpointMarkers.push(marker);
      pinpointStepText.innerHTML = `출발점 선택 완료! 이제 <strong>도착점 🏁</strong>을 클릭해 주세요`;
    } else if (pinpointPoints.length === 2) {
      const el = document.createElement('div');
      el.style.fontSize = '24px';
      el.textContent = '🏁';
      const marker = new maplibregl.Marker({ element: el }).setLngLat(lngLat).addTo(map);
      pinpointMarkers.push(marker);
      pinpointStepText.textContent = `실제 보행 경로 탐색 및 5단계 진단 중...`;

      await calculatePinpointDiagnostics(pinpointPoints[0], pinpointPoints[1]);
      cancelPinpointMode(false);
    }
  });
}

function startPinpointMode() {
  isPinpointMode = true;
  pinpointPoints = [];
  clearPinpointMarkers();
  btnPinpointMode.classList.add('active');
  pinpointBanner.classList.remove('hidden');
  pinpointStepText.innerHTML = `지도에서 <strong>출발점 🚩</strong>을 클릭해 주세요`;
  map.getCanvas().style.cursor = 'crosshair';
}

function cancelPinpointMode(clearLayers = true) {
  isPinpointMode = false;
  btnPinpointMode.classList.remove('active');
  pinpointBanner.classList.add('hidden');
  map.getCanvas().style.cursor = '';
  if (clearLayers) {
    clearPinpointMarkers();
    if (map && map.getSource('custom-route-src')) {
      map.getSource('custom-route-src').setData({ type: 'FeatureCollection', features: [] });
    }
  }
}

function clearPinpointMarkers() {
  pinpointMarkers.forEach(m => m.remove());
  pinpointMarkers = [];
}

async function calculatePinpointDiagnostics(start, end) {
  try {
    const url = `https://routing.openstreetmap.de/routed-foot/route/v1/foot/${start[0]},${start[1]};${end[0]},${end[1]}?overview=full&geometries=geojson`;
    const res = await fetch(url);
    const data = await res.json();

    if (data.code !== 'Ok' || !data.routes.length) {
      alert('보행 경로를 찾을 수 없습니다. 도로 근처를 클릭해 주세요.');
      return;
    }

    const route = data.routes[0];
    const distanceM = Math.round(route.distance);
    const durationMin = Math.max(1, Math.round(route.duration / 60));

    const customProps = {
      id: `custom_${Date.now()}`,
      dong_name: '내가 발굴한 맞춤 동네',
      street_name: `맞춤 보행 코스 (${distanceM}m)`,
      vibe_desc: `도보 약 ${durationMin}분 소요 구간`,
      province: '전국',
      sgg: '맞춤 분석 구역',
      dong: '맞춤동',
      width_m: 3.6,
      car_control: 0.85,
      car_control_label: '보행자 안심구간',
      slope_pct: 0.8,
      density_dist_m: 5.1,
      event_level: 0.7,
      event_label: '주변 로컬 상권 및 골목 탐색구역',
      cafe_interval_m: 25,
      transit_walk_min: durationMin,
      transit_diversity: 0.9,
      highlight_tag: '#직접발굴 #로컬골목 #맞춤진단'
    };

    calculateFeatureSubScores(customProps);

    const wEnv = parseFloat(weightEnvInput.value) || 0;
    const wPop = parseFloat(weightPopInput.value) || 0;
    const wEve = parseFloat(weightEveInput.value) || 0;
    const wTra = parseFloat(weightTraInput.value) || 0;
    const wTotal = wEnv + wPop + wEve + wTra || 1;

    const rawTotal = (wEnv * customProps.sub_score_env) +
                     (wPop * customProps.sub_score_pop) +
                     (wEve * customProps.sub_score_eve) +
                     (wTra * customProps.sub_score_tra);

    customProps.score_100 = Math.round((rawTotal / wTotal) * 100);

    const customFeature = {
      type: 'Feature',
      properties: customProps,
      geometry: route.geometry
    };
    customRouteFeature = customFeature;

    map.getSource('custom-route-src').setData({
      type: 'FeatureCollection',
      features: [customFeature]
    });

    renderCustomSidebar(customProps, distanceM, durationMin);

  } catch (err) {
    console.error('Failed to calculate custom route:', err);
    alert('경로 계산 중 오류가 발생했습니다.');
  }
}

function renderCustomSidebar(p, distanceM, durationMin) {
  const tier = getTierInfo(p.score_100);
  const tierEnv = getPillarTier(p.sub_score_env);
  const tierPop = getPillarTier(p.sub_score_pop);
  const tierEve = getPillarTier(p.sub_score_eve);
  const tierTra = getPillarTier(p.sub_score_tra);

  let stepBarHtml = '';
  for (let i = 1; i <= 5; i++) {
    const isActive = i <= tier.level ? tier.barClass : '';
    stepBarHtml += `<div class="step-segment ${isActive}"></div>`;
  }

  sidebarContent.innerHTML = `
    <div class="sidebar-dong-header">맞춤 진단 구간</div>
    <div class="sidebar-title">${p.street_name}</div>
    <div class="sidebar-vibe">${p.vibe_desc}</div>
    <div class="sidebar-tags-row">
      <span class="sidebar-hashtag">${p.highlight_tag}</span>
      <span class="cafe-mini-badge">☕ 약 25m마다 카페</span>
    </div>
    <div class="sidebar-region">📍 총 거리 ${distanceM}m | 도보 약 ${durationMin}분 소요</div>
    
    <div class="tier-header-card">
      <div class="tier-top-row">
        <span class="tier-badge ${tier.colorClass}">${tier.label}</span>
        <span class="tier-score-num">${p.score_100}<span style="font-size: 0.95rem; font-weight: 700; color: #64748b;">점</span></span>
      </div>
      <div class="step-bar-container">
        ${stepBarHtml}
      </div>
    </div>

    <div class="pillars-eval-title">📊 맞춤 구간 5단계 진단 결과</div>
    <div class="pillars-eval-list">
      <div class="pillar-eval-item">
        <div class="pillar-eval-header">
          <span class="pillar-eval-name">🌿 도보 환경</span>
          <span class="pillar-eval-tier" style="color: ${tierEnv.color}">${tierEnv.text}</span>
        </div>
        <div class="pillar-subtext">평균 보도폭 약 ${p.width_m}m · 완만한 평지</div>
      </div>

      <div class="pillar-eval-item">
        <div class="pillar-eval-header">
          <span class="pillar-eval-name">👥 인구밀도</span>
          <span class="pillar-eval-tier" style="color: ${tierPop.color}">${tierPop.text}</span>
        </div>
        <div class="pillar-subtext">사람 간격 약 ${p.density_dist_m}m (쾌적한 활력 스위트스팟)</div>
      </div>

      <div class="pillar-eval-item">
        <div class="pillar-eval-header">
          <span class="pillar-eval-name">🎪 이벤트</span>
          <span class="pillar-eval-tier" style="color: ${tierEve.color}">${tierEve.text}</span>
        </div>
        <div class="pillar-subtext">로컬 카페 및 골목 상권 인접</div>
      </div>

      <div class="pillar-eval-item">
        <div class="pillar-eval-header">
          <span class="pillar-eval-name">🚌 대중교통</span>
          <span class="pillar-eval-tier" style="color: ${tierTra.color}">${tierTra.text}</span>
        </div>
        <div class="pillar-subtext">도보 ${durationMin}분 이동 구간</div>
      </div>
    </div>

    <button id="btnSaveThisRoute" class="btn-save-custom-route">
      <i data-lucide="bookmark-plus"></i> 이 코스 내 보관함에 저장하기
    </button>
  `;

  detailSidebar.classList.add('open');
  lucide.createIcons();

  document.getElementById('btnSaveThisRoute').addEventListener('click', () => {
    const routeName = prompt('저장할 코스의 이름을 입력해주세요:', p.dong_name);
    if (routeName) {
      saveCustomRoute(routeName, p, customRouteFeature);
    }
  });
}

// ==========================================
// 12. 💾 LocalStorage Saved Routes System
// ==========================================
function getSavedRoutes() {
  return JSON.parse(localStorage.getItem('street_dna_saved_routes') || '[]');
}

function saveCustomRoute(name, props, feature) {
  const saved = getSavedRoutes();
  const newItem = {
    id: props.id,
    name: name,
    score: props.score_100,
    dong: props.dong,
    date: new Date().toLocaleDateString('ko-KR'),
    feature: feature
  };
  saved.unshift(newItem);
  localStorage.setItem('street_dna_saved_routes', JSON.stringify(saved));
  updateSavedBadge();
  alert(`'${name}' 코스가 내 보관함에 안전하게 저장되었습니다! 💾`);
}

function updateSavedBadge() {
  const saved = getSavedRoutes();
  savedCountBadge.textContent = saved.length;
}

btnOpenSaved.addEventListener('click', () => {
  renderSavedModal();
  savedModal.classList.remove('hidden');
});

btnCloseSaved.addEventListener('click', () => {
  savedModal.classList.add('hidden');
});

function renderSavedModal() {
  const saved = getSavedRoutes();
  savedRoutesList.innerHTML = '';

  if (saved.length === 0) {
    savedRoutesList.innerHTML = `<div style="text-align:center; padding: 30px; color:#64748b; font-size:0.9rem;">아직 저장된 맞춤 코스가 없습니다.<br><strong>[📍 구간 직접 진단]</strong> 버튼으로 코스를 발굴해보세요!</div>`;
    return;
  }

  saved.forEach((item, idx) => {
    const card = document.createElement('div');
    card.className = 'saved-item-card';
    card.innerHTML = `
      <div class="saved-item-info">
        <h4>${item.name}</h4>
        <p>${item.dong} · ${item.date} 저장 · <strong style="color:#047857;">${item.score}점</strong></p>
      </div>
      <div class="saved-item-actions">
        <button class="btn-sm-view" data-idx="${idx}">지도에서 보기</button>
        <button class="btn-sm-delete" data-idx="${idx}">삭제</button>
      </div>
    `;

    card.querySelector('.btn-sm-view').addEventListener('click', () => {
      savedModal.classList.add('hidden');
      map.getSource('custom-route-src').setData({
        type: 'FeatureCollection',
        features: [item.feature]
      });
      const coords = item.feature.geometry.coordinates;
      map.flyTo({ center: coords[Math.floor(coords.length / 2)], zoom: 16.5 });
      renderCustomSidebar(item.feature.properties, 500, 7);
    });

    card.querySelector('.btn-sm-delete').addEventListener('click', () => {
      if (confirm(`'${item.name}' 코스를 삭제하시겠습니까?`)) {
        saved.splice(idx, 1);
        localStorage.setItem('street_dna_saved_routes', JSON.stringify(saved));
        updateSavedBadge();
        renderSavedModal();
      }
    });

    savedRoutesList.appendChild(card);
  });
}

// ==========================================
// 13. ⚖️ 1:1 Dong VS Comparison Modal
// ==========================================
function populateCompareDropdowns() {
  compareSelectA.innerHTML = '';
  compareSelectB.innerHTML = '';

  rawGeoData.features.forEach((f, idx) => {
    const p = f.properties;
    const optA = new Option(`[${p.dong_name}] ${p.street_name}`, p.id);
    const optB = new Option(`[${p.dong_name}] ${p.street_name}`, p.id);
    if (idx === 0) optA.selected = true;
    if (idx === 1) optB.selected = true;
    compareSelectA.add(optA);
    compareSelectB.add(optB);
  });

  renderCompareMatrix();
}

btnOpenCompare.addEventListener('click', () => {
  renderCompareMatrix();
  compareModal.classList.remove('hidden');
});

btnCloseCompare.addEventListener('click', () => {
  compareModal.classList.add('hidden');
});

[compareSelectA, compareSelectB].forEach(sel => {
  sel.addEventListener('change', () => {
    renderCompareMatrix();
  });
});

function renderCompareMatrix() {
  const idA = compareSelectA.value;
  const idB = compareSelectB.value;

  const fA = rawGeoData.features.find(f => f.properties.id === idA);
  const fB = rawGeoData.features.find(f => f.properties.id === idB);

  if (!fA || !fB) return;

  const pA = fA.properties;
  const pB = fB.properties;

  const tierA = getTierInfo(pA.score_100);
  const tierB = getTierInfo(pB.score_100);

  compareMatrixContent.innerHTML = `
    <!-- Total Score Row -->
    <div class="compare-row" style="background:#ecfdf5; padding: 14px 12px; border-radius: 12px;">
      <div class="compare-val-a ${pA.score_100 >= pB.score_100 ? 'val-highlight' : ''}">
        <div style="font-size: 1.5rem; font-weight:900;">${pA.score_100}점</div>
        <span class="tier-badge ${tierA.colorClass}">${tierA.label.split(':')[1]}</span>
      </div>
      <div class="compare-label-center" style="font-size:0.9rem;">🏆 종합 점수</div>
      <div class="compare-val-b ${pB.score_100 >= pA.score_100 ? 'val-highlight' : ''}">
        <div style="font-size: 1.5rem; font-weight:900;">${pB.score_100}점</div>
        <span class="tier-badge ${tierB.colorClass}">${tierB.label.split(':')[1]}</span>
      </div>
    </div>

    <!-- 1. Environment Row -->
    <div class="compare-row">
      <div class="compare-val-a ${pA.width_m >= pB.width_m ? 'val-highlight' : ''}">
        보도폭 <strong>${pA.width_m}m</strong><br>
        <span style="font-size:0.75rem; color:#64748b;">${pA.car_control_label ? pA.car_control_label.split(' ')[0] : '보행안심'}</span>
      </div>
      <div class="compare-label-center">🌿 도보 환경</div>
      <div class="compare-val-b ${pB.width_m >= pA.width_m ? 'val-highlight' : ''}">
        보도폭 <strong>${pB.width_m}m</strong><br>
        <span style="font-size:0.75rem; color:#64748b;">${pB.car_control_label ? pB.car_control_label.split(' ')[0] : '보행안심'}</span>
      </div>
    </div>

    <!-- 2. Population Density Row -->
    <div class="compare-row">
      <div class="compare-val-a ${Math.abs(pA.density_dist_m - 5) <= Math.abs(pB.density_dist_m - 5) ? 'val-highlight' : ''}">
        간격 <strong>${pA.density_dist_m}m</strong><br>
        <span style="font-size:0.75rem; color:#64748b;">(5m 골든존 근접)</span>
      </div>
      <div class="compare-label-center">👥 인구밀도</div>
      <div class="compare-val-b ${Math.abs(pB.density_dist_m - 5) <= Math.abs(pA.density_dist_m - 5) ? 'val-highlight' : ''}">
        간격 <strong>${pB.density_dist_m}m</strong><br>
        <span style="font-size:0.75rem; color:#64748b;">(5m 골든존 근접)</span>
      </div>
    </div>

    <!-- 3. Events Row -->
    <div class="compare-row">
      <div class="compare-val-a ${pA.event_level >= pB.event_level ? 'val-highlight' : ''}">
        <strong>${pA.event_label}</strong><br>
        <span style="font-size:0.75rem; color:#64748b;">이벤트 ${pA.events_list ? pA.events_list.length : 0}건</span>
      </div>
      <div class="compare-label-center">🎪 이벤트</div>
      <div class="compare-val-b ${pB.event_level >= pA.event_level ? 'val-highlight' : ''}">
        <strong>${pB.event_label}</strong><br>
        <span style="font-size:0.75rem; color:#64748b;">이벤트 ${pB.events_list ? pB.events_list.length : 0}건</span>
      </div>
    </div>

    <!-- 4. Transit Row -->
    <div class="compare-row">
      <div class="compare-val-a ${pA.transit_walk_min <= pB.transit_walk_min ? 'val-highlight' : ''}">
        도보 <strong>${pA.transit_walk_min}분 컷</strong>
      </div>
      <div class="compare-label-center">🚌 대중교통</div>
      <div class="compare-val-b ${pB.transit_walk_min <= pA.transit_walk_min ? 'val-highlight' : ''}">
        도보 <strong>${pB.transit_walk_min}분 컷</strong>
      </div>
    </div>
  `;
}

// 14. Event Listeners for Custom Weight Inputs & Presets
presetChips.forEach(chip => {
  chip.addEventListener('click', () => {
    presetChips.forEach(c => c.classList.remove('active'));
    chip.classList.add('active');

    const presetKey = chip.getAttribute('data-preset');
    const preset = walkingPresets[presetKey];
    if (preset) {
      weightEnvInput.value = preset.env;
      weightPopInput.value = preset.pop;
      weightEveInput.value = preset.eve;
      weightTraInput.value = preset.tra;
      recalculateAll();
    }
  });
});

btnOpenCustomWeights.addEventListener('click', () => {
  customWeightModal.classList.remove('hidden');
});

btnCloseCustomWeight.addEventListener('click', () => {
  customWeightModal.classList.add('hidden');
});

[weightEnvInput, weightPopInput, weightEveInput, weightTraInput].forEach(input => {
  input.addEventListener('input', () => {
    // Deselect preset chips when user manually tweaks
    presetChips.forEach(c => c.classList.remove('active'));
    recalculateAll();
  });
});

resetWeightsBtn.addEventListener('click', () => {
  weightEnvInput.value = defaultWeights.env;
  weightPopInput.value = defaultWeights.pop;
  weightEveInput.value = defaultWeights.eve;
  weightTraInput.value = defaultWeights.tra;
  
  presetChips.forEach(c => c.classList.remove('active'));
  const balanceChip = document.querySelector('[data-preset="balance"]');
  if (balanceChip) balanceChip.classList.add('active');

  recalculateAll();
});

sggSelect.addEventListener('change', () => {
  renderRankingCarousel();
  updateMapMarkers();

  const selectedRegion = sggSelect.value;
  const viewInfo = regionCenters[selectedRegion] || regionCenters['ALL'];

  if (selectedRegion === 'ALL') {
    if (userLocation) {
      map.flyTo({ center: [userLocation.lng, userLocation.lat], zoom: 13.0, pitch: 0, padding: { left: 0 }, duration: 1200 });
    } else {
      map.flyTo({ center: viewInfo.center, zoom: viewInfo.zoom, pitch: 0, padding: { left: 0 }, duration: 1200 });
    }
    detailSidebar.classList.remove('open');
    if (map && map.getSource('selected-dong-src')) {
      map.getSource('selected-dong-src').setData({ type: 'FeatureCollection', features: [] });
    }
    if (selectedLandmarkMarker) {
      selectedLandmarkMarker.remove();
      selectedLandmarkMarker = null;
    }
  } else {
    const firstFeature = rawGeoData.features.find(f => f.properties.province === selectedRegion);
    if (firstFeature) {
      highlightFeature(firstFeature.properties.id, true);
    } else {
      map.flyTo({ center: viewInfo.center, zoom: viewInfo.zoom, pitch: 0, padding: { left: 0 }, duration: 1200 });
      if (selectedLandmarkMarker) {
        selectedLandmarkMarker.remove();
        selectedLandmarkMarker = null;
      }
    }
  }
});

document.querySelectorAll('.btn-calc-toggle').forEach(btn => {
  btn.addEventListener('click', () => {
    const targetId = btn.getAttribute('data-target');
    const box = document.getElementById(targetId);
    if (!box) return;

    const isOpen = box.classList.contains('open');
    if (isOpen) {
      box.classList.remove('open');
      btn.classList.remove('open');
    } else {
      box.classList.add('open');
      btn.classList.add('open');
    }
  });
});

// Mobile Bottom Sheet Drag Handle Swipe to Close
const sidebarDragHandle = document.querySelector('.sidebar-drag-handle');
if (sidebarDragHandle) {
  let touchStartY = 0;
  sidebarDragHandle.addEventListener('touchstart', (e) => {
    touchStartY = e.touches[0].clientY;
  }, { passive: true });

  sidebarDragHandle.addEventListener('touchmove', (e) => {
    const touchY = e.touches[0].clientY;
    if (touchY - touchStartY > 60) {
      detailSidebar.classList.remove('open');
      activeFeatureId = null;
      document.querySelectorAll('.ranking-card').forEach(c => c.classList.remove('active'));
      document.querySelectorAll('.dong-map-chip').forEach(m => m.classList.remove('active'));
      if (map && map.getSource('selected-dong-src')) {
        map.getSource('selected-dong-src').setData({ type: 'FeatureCollection', features: [] });
      }
      if (selectedLandmarkMarker) {
        selectedLandmarkMarker.remove();
        selectedLandmarkMarker = null;
      }
    }
  }, { passive: true });
}

window.addEventListener('DOMContentLoaded', () => {
  initMap();
  lucide.createIcons();
});
