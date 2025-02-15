let visualizationData;
let currentWeekIndex = 0;
let isPlaying = false;
let playPauseButton;
let weekSlider;
let lastTimestamp = 0;
const ANIMATION_SPEED = 5000; // Increased from 1000 to 5000ms (5 seconds per week)
let table;
let factor = 0;
let targetColors = [];
let currentColors = [];
let transitionProgress = 0;
const TRANSITION_DURATION = 4000; // Increased from 2000 to 4000ms (4 seconds for color transition)

// Noise configuration
let xScale = 0.015;
let yScale = 0.02;

// UI controls
let gapSlider;
let gap;
let offsetSlider;
let offset;

// Add easing function for smoother transitions
function easeInOutCubic(x) {
    return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
}

// Extended color palette with specific colors for each category
const colors = {
    // Core - Mora
    'mora': '#1F1051',  // 105,210,231

    // Close friends and family
    'clay': '#B7104D',  // 254,67,101
    'pau': '#7B1282',  // 236,151,135
    'sara': '#E5C5B5',  // 229,197,181
    'eden': '#E0CE8A',  // 224,206,138
    'gabo': '#D4A5A5',  // 212,165,165
    'jaime': '#C27C88',  // 194,124,136
    'isa': '#D8A7B1',  // 216,167,177
    'feli': '#E6B89C',  // 230,184,156
    'nara': '#D8B4A0',  // 216,180,160
    'marie': '#D4BBB1',  // 212,187,177
    'pipia': '#E5C1B1',  // 229,193,177
    'ana_valeria': '#DDB7A0',  // 221,183,160
    'stacy': '#E6C3B0',  // 230,195,176
    'trinity': '#D6B8A8',  // 214,184,168
    'marianna': '#E2BBA6',  // 226,187,166
    'parents': '#D4A599',  // 212,165,153
    'miranda': '#E8C1B4',  // 232,193,180
    'eloise': '#DFB5A3',  // 223,181,163
    'hayes': '#E5B8A6',  // 229,184,166
    'emily': '#D8AFA0',  // 216,175,160
    'perry': '#E2B8A8',  // 226,184,168
    'leslie': '#DFAC9C',  // 223,172,156
    'ana': '#E5B5A5',  // 229,181,165
    'leila': '#D6A99B',  // 214,169,155
    'alex': '#E2AFA1',  // 226,175,161
    'nina': '#D8A697',  // 216,166,151
    'mariela': '#E5BFB1',  // 229,191,177

    // Love and affection
    'love_expressions': '#E79F23',  // 255,66,66
    'terms_of_endearment': '#F4FAD2',  // 244,250,210
    'missing_each_other': '#D4EE5E',  // 212,238,94
    'cuddles': '#E1EDB9',  // 225,237,185
    'besito': '#F0F2EB',  // 240,242,235

    // Emotional states
    'happiness': '#FFD1DC',  // 255,209,220
    'sadness': '#B5A8A8',  // 181,168,168
    'worry': '#A69999',  // 166,153,153

    // Daily life
    'home_life': '#7AB80E',  // 122,184,14
    'food': '#B4C7D9',  // 180,199,217
    'sleep': '#5C98C4',  // 92,152,196
    'work': '#B59C8C',  // 181,156,140
    'bathroom': '#A68C7F',  // 166,140,127

    // Special moments
    'celebration': '#FE9600',  // 254,150,0
    'plans': '#FFC100',  // 255,193,0

    // Shared language
    'custom_expressions': '#97C0E3',  // 151,192,227
    'laughter': '#F1977E',  // 181,165,165

    // Default
    'default': '#D4C1C1'  // 212,193,193
};

// Initialize fixed positions for categories
function initializeCategoryPositions() {
    const categories = Object.keys(colors);
    const cols = 5;
    const rows = Math.ceil(categories.length / cols);
    const cellWidth = width / cols;
    const cellHeight = height / rows;
    
    categories.forEach((category, index) => {
        const col = index % cols;
        const row = Math.floor(index / cols);
        // Store base position with some randomness
        categoryPositions.set(category, {
            x: cellWidth * (col + 0.5) + random(-cellWidth * 0.2, cellWidth * 0.2),
            y: cellHeight * (row + 0.5) + random(-cellHeight * 0.2, cellHeight * 0.2)
        });
    });
}

function preload() {
    console.log('Starting preload...');
    loadJSON('weekly_visualization_data.json', data => {
        console.log('Data loaded:', data);
        visualizationData = data;
        currentWeekIndex = findNextValidWeekIndex(0);
        setupSlider();
    });
    table = loadTable("colors.csv", "csv", "header");
}

function setupSlider() {
    weekSlider = select('#week-slider');
    weekSlider.attribute('max', visualizationData.timeline.length - 1);
    weekSlider.value(currentWeekIndex);
    weekSlider.input(() => {
        currentWeekIndex = parseInt(weekSlider.value());
        updateDateDisplay();
        updateInfoDisplays();
        initializeColorTransition();
    });
    updateDateDisplay();
    updateInfoDisplays();
}

function updateDateDisplay() {
    const weekData = visualizationData.timeline[currentWeekIndex];
    if (weekData) {
        const weekStart = new Date(weekData.week_start);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        const dateStr = `${weekStart.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}`;
        select('#current-date').html(dateStr);
    }
}

function updateInfoDisplays() {
    const weekData = visualizationData.timeline[currentWeekIndex];
    if (!weekData || !weekData.senders) return;

    // Combine data from both senders
    const combinedCategories = {};
    Object.values(weekData.senders).forEach(senderData => {
        // Combine categories
        Object.entries(senderData.word_categories || {}).forEach(([category, count]) => {
            combinedCategories[category] = (combinedCategories[category] || 0) + count;
        });
    });

    // Update legend
    const categoryLegend = select('#category-legend');
    categoryLegend.html('');
    
    // Sort categories by count and take top 5
    const sortedCategories = Object.entries(combinedCategories)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5);

    // Create legend items
    sortedCategories.forEach(([category, count], index) => {
        const legendItem = createElement('div');
        legendItem.class('legend-item');
        
        const colorDot = createElement('div');
        colorDot.class('color-dot');
        const color = colors[category] || colors['default'];
        colorDot.style('background-color', color);
        
        const label = createElement('div');
        label.class('legend-label');
        label.html(category.replace(/_/g, ' '));
        
        const countSpan = createElement('div');
        countSpan.class('legend-count');
        countSpan.html(count);
        
        legendItem.child(colorDot);
        legendItem.child(label);
        legendItem.child(countSpan);
        categoryLegend.child(legendItem);
    });
}

function setup() {
    console.log('Setting up...');
    const canvas = createCanvas(windowWidth * 0.6, windowHeight * 0.6);
    canvas.parent('canvas-container');
    
    playPauseButton = select('#play-pause');
    playPauseButton.mousePressed(togglePlayPause);
    
    noStroke();
    noiseSeed(random(1000));
    
    isPlaying = true;
    playPauseButton.html('Pause');
    
    initializeColorTransition();

    // Set up the sliders
    gapSlider = createSlider(2, width / 10, width / 20);
    gapSlider.parent('canvas-container');
    gapSlider.style('width', '200px');
    gapSlider.style('margin', '10px');
    
    offsetSlider = createSlider(0, 1000, 0);
    offsetSlider.parent('canvas-container');
    offsetSlider.style('width', '200px');
    offsetSlider.style('margin', '10px');

    // Initial draw
    dotGrid();
}

function initializeColorTransition() {
    const weekData = visualizationData.timeline[currentWeekIndex];
    if (!weekData || !weekData.senders) return;

    // Get combined categories
    const combinedCategories = {};
    Object.values(weekData.senders).forEach(senderData => {
        if (!senderData || !senderData.word_categories) return;
        Object.entries(senderData.word_categories).forEach(([category, count]) => {
            combinedCategories[category] = (combinedCategories[category] || 0) + count;
        });
    });

    // Sort categories by count
    const sortedCategories = Object.entries(combinedCategories)
        .sort(([,a], [,b]) => b - a);
    
    // Calculate total messages to determine color diversity
    const totalMessages = sortedCategories.reduce((sum, [,count]) => sum + count, 0);
    
    // Determine how many categories to include based on message volume
    // More messages = more color variety
    const maxCategories = Math.min(
        Math.max(3, Math.floor(Math.sqrt(totalMessages / 10))), 
        sortedCategories.length
    );
    
    // Store current colors as starting point
    currentColors = targetColors.length ? [...targetColors] : getColorsFromPalette(0);

    // Set new target colors based on categories
    targetColors = [];
    sortedCategories.slice(0, maxCategories).forEach(([category, count], index) => {
        // Number of colors per category based on its relative importance
        const categoryWeight = count / totalMessages;
        const colorsForCategory = Math.max(1, Math.floor(categoryWeight * 5));
        
        // Get colors for this category
        for (let i = 0; i < colorsForCategory; i++) {
            const paletteIndex = Math.floor(random(table.getRowCount()));
            targetColors.push(...getColorsFromPalette(paletteIndex));
        }
    });

    // Ensure minimum number of colors
    while (targetColors.length < 3) {
        const paletteIndex = Math.floor(random(table.getRowCount()));
        targetColors.push(...getColorsFromPalette(paletteIndex));
    }

    // Cap maximum number of colors to prevent overwhelming visuals
    if (targetColors.length > 15) {
        targetColors = targetColors.slice(0, 15);
    }

    // Reset transition
    transitionProgress = 0;
}

function getColorsFromPalette(rowIndex) {
    const colors = [];
    for (let i = 0; i < 3; i++) {
        colors.push({
            r: int(table.get(rowIndex, i * 3)),
            g: int(table.get(rowIndex, i * 3 + 1)),
            b: int(table.get(rowIndex, i * 3 + 2))
        });
    }
    return colors;
}

function draw() {
    // Update transition progress with easing
    if (transitionProgress < 1) {
        transitionProgress = min(1, transitionProgress + (deltaTime / TRANSITION_DURATION));
        // Apply easing to the transition
        const easedProgress = easeInOutCubic(transitionProgress);
        
        // Slow down the perlin noise animation during transitions
        factor += 0.001 * (1 - easedProgress); // Slower movement during transitions
    } else {
        factor += 0.002; // Normal speed when not transitioning
    }

    // Clear with a semi-transparent light background
    background(230, 209, 209, 20);
    
    if (!visualizationData || !visualizationData.timeline[currentWeekIndex]) return;
    
    const currentTime = millis();
    if (isPlaying && currentTime - lastTimestamp > ANIMATION_SPEED) {
        currentWeekIndex = findNextValidWeekIndex(currentWeekIndex);
        weekSlider.value(currentWeekIndex);
        updateDateDisplay();
        updateInfoDisplays();
        initializeColorTransition();
        lastTimestamp = currentTime;
    }
    
    drawPerlinField();
}

function drawPerlinField() {
    const rez1 = 0.002; // Perlin noise resolution
    const rez2 = 0.004;
    factor += 0.002; // Speed of animation

    for (let i = 0; i < width; i += 4) {
        for (let j = 0; j < height; j += 4) {
            if (random(10) < 0.8) {
                let n1 = noise(i * rez1 + factor, j * rez1 + factor);
                let n2 = noise(i * rez2 + factor, j * rez2 + factor);
                
                // Use noise to determine which color to use, with smooth wrapping
                let colorIndex = floor(map((n1 + n2) / 2, 0, 1, 0, currentColors.length));
                let nextColorIndex = (colorIndex + 1) % currentColors.length;
                let blendFactor = ((n1 + n2) / 2 * currentColors.length) % 1;
                
                // Get current colors
                let currentColor1 = currentColors[colorIndex % currentColors.length];
                let currentColor2 = currentColors[nextColorIndex];
                let targetColor1 = targetColors[colorIndex % targetColors.length];
                let targetColor2 = targetColors[nextColorIndex % targetColors.length];
                
                // Interpolate between current and target colors
                let r1 = lerp(currentColor1.r, targetColor1.r, transitionProgress);
                let g1 = lerp(currentColor1.g, targetColor1.g, transitionProgress);
                let b1 = lerp(currentColor1.b, targetColor1.b, transitionProgress);
                
                let r2 = lerp(currentColor2.r, targetColor2.r, transitionProgress);
                let g2 = lerp(currentColor2.g, targetColor2.g, transitionProgress);
                let b2 = lerp(currentColor2.b, targetColor2.b, transitionProgress);
                
                // Blend between adjacent colors
                let r = lerp(r1, r2, blendFactor);
                let g = lerp(g1, g2, blendFactor);
                let b = lerp(b1, b2, blendFactor);
                
                noStroke();
                fill(r, g, b, 130);
                
                // Draw organic shapes
                beginShape();
                for (let m = 0; m < TWO_PI; m += 0.5) {
                    let radius = random(4, 7);
                    let x = cos(m) * radius + i;
                    let y = sin(m) * radius + j;
                    vertex(x, y);
                }
                endShape(CLOSE);
            }
        }
    }
}

function hasMessages(weekData) {
    if (!weekData || !weekData.senders) return false;
    return Object.values(weekData.senders).some(sender => 
        sender && sender.message_count && sender.message_count > 0
    );
}

function findNextValidWeekIndex(currentIndex, direction = 1) {
    if (!visualizationData || !visualizationData.timeline) return currentIndex;
    
    let nextIndex = currentIndex;
    let checkedCount = 0;
    
    while (checkedCount < visualizationData.timeline.length) {
        nextIndex = (nextIndex + direction + visualizationData.timeline.length) % visualizationData.timeline.length;
        if (hasMessages(visualizationData.timeline[nextIndex])) {
            return nextIndex;
        }
        checkedCount++;
    }
    
    return currentIndex;
}

function togglePlayPause() {
    isPlaying = !isPlaying;
    playPauseButton.html(isPlaying ? 'Pause' : 'Play');
}

function windowResized() {
    resizeCanvas(windowWidth * 0.6, windowHeight * 0.6);
    dotGrid();
}

// When the mouse is moved over a slider
// Draw the dot grid if something has changed
function checkChanged() {
    if (gap !== gapSlider.value()) {
        dotGrid();
    }
    if (offset !== offsetSlider.value()) {
        dotGrid();
    }
}

function dotGrid() {
    background(255);
    noStroke();
    fill(0);

    // Get the current gap and offset values from the sliders
    gap = gapSlider.value();
    offset = offsetSlider.value();

    // Loop through x and y coordinates, at increments set by gap
    for (let x = gap / 2; x < width; x += gap) {
        for (let y = gap / 2; y < height; y += gap) {
            // Calculate noise value using scaled and offset coordinates
            let noiseValue = noise((x + offset) * xScale, (y + offset) * yScale);

            // Since noiseValue will be 0-1, multiply it by gap to set diameter to
            // between 0 and the size of the gap between circles
            let diameter = noiseValue * gap;
            circle(x, y, diameter);
        }
    }
} 