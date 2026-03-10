// 1. Study area
var roi = ee.Geometry.Rectangle([23,60,26,62]);
Map.centerObject(roi, 7);
Map.addLayer(roi, {color: 'red'}, 'ROI');

// 2. Time
var year = 2023;
var startMonth = 4;   // April
var endMonth = 10;    // October

var months = ee.List.sequence(startMonth, endMonth);

// 3. Load datasets
// MODIS EVI
var modis = ee.ImageCollection('MODIS/061/MOD13Q1')
  .filterBounds(roi)
  .select('EVI')
  .map(function(img) {
    return img.multiply(0.0001)
      .copyProperties(img, ['system:time_start']);
  });

// ERA5-Land daily aggregated solar radiation
var era5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR')
  .filterBounds(roi)
  .select('surface_solar_radiation_downwards_sum');

// 4. Visualization
var eviVis = {
  min: 0.1,
  max: 0.7,
  palette: ['brown', 'yellow', 'lightgreen', 'green', 'darkgreen']
};

var radVis = {
  min: 1.0e7,
  max: 3.0e7,
  palette: ['blue', 'yellow', 'red']
};

// 5. Export monthly images
months.getInfo().forEach(function(m) {
  var monthStart = ee.Date.fromYMD(year, m, 1);
  var monthEnd = monthStart.advance(1, 'month');
  var monthStr = ee.Number(m).format('%02d').getInfo();

  // Monthly mean EVI
  var monthlyEVI = modis
    .filterDate(monthStart, monthEnd)
    .mean()
    .clip(roi)
    .rename('EVI');

  // Monthly mean solar radiation
  var monthlyRad = era5
    .filterDate(monthStart, monthEnd)
    .mean()
    .clip(roi)
    .rename('SSR');

  // Add to map
  Map.addLayer(monthlyEVI, eviVis, 'EVI_' + year + '_' + monthStr, false);
  Map.addLayer(monthlyRad, radVis, 'SSR_' + year + '_' + monthStr, false);

  // Export EVI
  Export.image.toDrive({
    image: monthlyEVI,
    description: 'EVI_' + year + '_' + monthStr,
    folder: 'GEE_monthly_exports',
    fileNamePrefix: 'EVI_' + year + '_' + monthStr,
    region: roi,
    scale: 250,
    crs: 'EPSG:3067',
    maxPixels: 1e13
  });

  // Export solar radiation
  Export.image.toDrive({
    image: monthlyRad,
    description: 'SSR_' + year + '_' + monthStr,
    folder: 'GEE_monthly_exports',
    fileNamePrefix: 'SSR_' + year + '_' + monthStr,
    region: roi,
    scale: 10000,
    crs: 'EPSG:3067',
    maxPixels: 1e13
  });
});