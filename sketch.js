// Visualization data
let visualizationData;
let messageQueue = [];
let lastMessageTime = 0;
const MESSAGE_INTERVAL = 2000;  // Increased from 500 to 2000ms
const MONTH_TRANSITION_DELAY = 5000;  // 5 second delay between months
let currentMonth = '';
let isTransitioning = false;
let transitionStartTime = 0;

// Particle settings
const PARTICLE_COUNT = 20000;
const NOISE_SCALE = 0.01;
const PARTICLE_SIZE = 3.5;  // Added size parameter
let particles = [];

// Simplified color mapping
const PEOPLE_COLORS = {
    'clay': [255, 105, 180],      // Hot Pink
    'pau': [102, 51, 153],       // Deep Purple
    'eden': [144, 238, 144],      // Light Green
    'sara': [255, 218, 185],      // Peach
    'emily': [221, 160, 221],     // Plum
    'stacy': [255, 160, 122],     // Light Coral
    'ana_valeria': [176, 224, 230],// Powder Blue
    'parents': [255, 192, 203],    // Pink
    'isa': [221, 160, 221],       // Plum
    'gabo': [255, 0, 0],      // Strong Red
    'pipia': [238, 130, 238],     // Violet
    'leslie': [135, 206, 235],    // Sky Blue
    'feli': [255, 160, 122],      // Light Coral
    'default': [15, 82, 186],
    'alex': [173, 216, 230],      // Light Blue
};

let isDataLoaded = false;

class Particle {
    constructor() {
        this.pos = createVector(random(width), random(height));
        this.color = PEOPLE_COLORS.default;
    }

    update() {
        let n = noise(this.pos.x * NOISE_SCALE, this.pos.y * NOISE_SCALE);
        let angle = TAU * n;
        this.pos.x += cos(angle);
        this.pos.y += sin(angle);

        if (!this.onScreen()) {
            this.pos.x = random(width);
            this.pos.y = random(height);
        }
    }

    show() {
        stroke(this.color[0], this.color[1], this.color[2], 50);
        strokeWeight(PARTICLE_SIZE);  // Using the new size parameter
        point(this.pos.x, this.pos.y);
    }

    onScreen() {
        return this.pos.x >= 0 && this.pos.x <= width && 
               this.pos.y >= 0 && this.pos.y <= height;
    }
}

function preload() {
    try {
        loadJSON('monthly_visualization_data.json', 
            data => {
                console.log("Data loaded successfully");
                if (data && Object.keys(data).length > 0) {
                    visualizationData = data;
                    const firstMonth = Object.keys(data)[0];
                    currentMonth = firstMonth;
                    isDataLoaded = true;
                    populateMonthSelector();
                } else {
                    console.error("No data found in visualization data");
                }
            },
            error => {
                console.error("Error loading JSON:", error);
            }
        );
    } catch (e) {
        console.error("Error in preload:", e);
    }
}

function setup() {
    const canvas = createCanvas(windowWidth * 0.8, windowHeight * 0.7);
    canvas.parent('canvas-container');
    
    pixelDensity(1);
    frameRate(30);
    
    // Initialize particles
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles[i] = new Particle();
    }
    
    // Set initial background
    background(0);
    
    // Initialize message queue if data is loaded
    if (isDataLoaded && visualizationData && currentMonth) {
        createMessageQueue(visualizationData[currentMonth]);
        updateMonthTitle(currentMonth);
    }
    
    lastMessageTime = millis();
}

function draw() {
    if (!isDataLoaded) return;

    background(0, 10);
    
    // Update and draw particles
    for (let particle of particles) {
        particle.update();
        particle.show();
    }
    
    // Update messages
    const currentTime = millis();
    if (currentTime - lastMessageTime > MESSAGE_INTERVAL) {
        addNextMessage();
        lastMessageTime = currentTime;
    }
}

function windowResized() {
    resizeCanvas(windowWidth * 0.8, windowHeight * 0.7);
    background(0);
}

function mousePressed() {
    noiseSeed(millis());
}

function createMessageQueue(monthData) {
    messageQueue = []; // Clear existing queue
    let messageOrder = 0;
    
    // Update particle colors based on the new month's data
    updateParticleColors(monthData);
    
    // Use the current month instead of the first month
    const monthDate = currentMonth;
    
    // Add emoji messages for Luz
    if (monthData.top_emojis && monthData.top_emojis.luz) {
        Object.entries(monthData.top_emojis.luz).forEach(([emoji, count]) => {
            messageQueue.push({
                type: 'emoji',
                content: emoji,
                count: count,
                sender: 'Luz',
                messageOrder: messageOrder++,
                monthDate: monthDate
            });
        });
    }
    
    // Add emoji messages for Andrea
    if (monthData.top_emojis && monthData.top_emojis.andrea) {
        Object.entries(monthData.top_emojis.andrea).forEach(([emoji, count]) => {
            messageQueue.push({
                type: 'emoji',
                content: emoji,
                count: count,
                sender: 'Andrea',
                messageOrder: messageOrder++,
                monthDate: monthDate
            });
        });
    }
    
    // Add special word messages
    if (monthData.special_words) {
        Object.entries(monthData.special_words).forEach(([word, count]) => {
            if (count > 0) {
                messageQueue.push({
                    type: 'word',
                    content: word,
                    count: count,
                    sender: messageOrder % 2 === 0 ? 'Luz' : 'Andrea',
                    messageOrder: messageOrder++,
                    monthDate: monthDate
                });
            }
        });
    }
    
    // Sort messages by messageOrder to maintain sequence
    messageQueue.sort((a, b) => a.messageOrder - b.messageOrder);
}

function formatMonthDate(monthDate) {
    const date = new Date(monthDate);
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

function updateMonthTitle(monthDate) {
    const formattedDate = formatMonthDate(monthDate);
    const titleElement = document.getElementById('current-month');
    const monthSelector = document.getElementById('month-selector');
    
    if (titleElement) {
        titleElement.textContent = formattedDate;
    }
    
    if (monthSelector && monthSelector.value !== monthDate) {
        monthSelector.value = monthDate;
    }
}

function addNextMessage() {
    if (messageQueue.length === 0) {
        if (!isTransitioning) {
            // Start transition to next month
            isTransitioning = true;
            transitionStartTime = millis();
            return;
        }
        
        // Check if we've waited long enough
        if (millis() - transitionStartTime < MONTH_TRANSITION_DELAY) {
            return;
        }
        
        // Reset transition state
        isTransitioning = false;
        
        // Get next month
        const months = Object.keys(visualizationData);
        const currentIndex = months.indexOf(currentMonth);
        const nextIndex = (currentIndex + 1) % months.length;
        const nextMonth = months[nextIndex];
        
        // Update current month and regenerate message queue
        currentMonth = nextMonth;
        createMessageQueue(visualizationData[nextMonth]);
        updateMonthTitle(nextMonth);
        
        // Add noise seed change on month transition
        noiseSeed(millis());
        return;
    }
    
    const message = messageQueue.shift();
    const chatMessages = document.getElementById('chat-messages');
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.sender.toLowerCase()}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    if (message.type === 'emoji') {
        messageContent.innerHTML = `
            <div class="message-sender">${message.sender}</div>
            <div class="message-emoji-container">
                <span class="message-emoji">${message.content}</span>
                <span class="message-count">×${message.count}</span>
            </div>
            <div class="message-time">${formatMonthDate(message.monthDate)}</div>
        `;
    } else {
        messageContent.innerHTML = `
            <div class="message-sender">${message.sender}</div>
            <p class="message-text">${message.content} <span class="message-count">(${message.count})</span></p>
            <div class="message-time">${formatMonthDate(message.monthDate)}</div>
        `;
    }
    
    messageElement.appendChild(messageContent);
    chatMessages.appendChild(messageElement);
    
    // Add show class after a brief delay to trigger animation
    requestAnimationFrame(() => {
        messageElement.classList.add('show');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

function updateParticleColors(monthData) {
    const people = monthData.people_mentions || {};
    const peopleList = Object.keys(people);
    
    // If no people mentioned, set all particles to default color
    if (peopleList.length === 0) {
        const defaultColor = PEOPLE_COLORS.default;
        for (let i = 0; i < particles.length; i++) {
            particles[i].color = defaultColor;
        }
        updatePeopleLegend([]);
        return;
    }

    // Calculate total mentions
    const totalMentions = Object.values(people).reduce((sum, count) => sum + count, 0);
    
    // Sort people by mention count and calculate particle distribution
    const sortedPeople = peopleList
        .sort((a, b) => people[b] - people[a])
        .map(person => ({
            name: person,
            color: PEOPLE_COLORS[person] || PEOPLE_COLORS.default,
            count: people[person],
            particles: Math.floor((people[person] / totalMentions) * PARTICLE_COUNT)
        }));

    // Assign colors to particles in a single pass
    let particleIndex = 0;
    for (const person of sortedPeople) {
        const endIndex = Math.min(particleIndex + person.particles, PARTICLE_COUNT);
        for (let i = particleIndex; i < endIndex; i++) {
            particles[i].color = person.color;
        }
        particleIndex = endIndex;
    }

    // Fill remaining particles with default color
    const defaultColor = PEOPLE_COLORS.default;
    for (let i = particleIndex; i < PARTICLE_COUNT; i++) {
        particles[i].color = defaultColor;
    }

    // Update legend
    updatePeopleLegend(sortedPeople);
}

function updatePeopleLegend(peopleData) {
    const legendContainer = document.getElementById('people-legend');
    if (!legendContainer) return;
    
    legendContainer.innerHTML = peopleData.length > 0 ? 
        `<h3>People We Texted About <3</h3>
        <div class="legend-items-container">
            ${peopleData.map(person => `
                <div class="legend-item">
                    <div class="color-dot" style="background-color: rgb(${person.color[0]}, ${person.color[1]}, ${person.color[2]})"></div>
                    <span class="legend-label">${person.name.replace('_', ' ')}</span>
                    <span class="legend-count">${person.count}</span>
                </div>
            `).join('')}
        </div>` :
        `<h3>People We Texted About <3</h3>
        <div class="legend-items-container">
            <div class="legend-item">
                <span class="legend-label">No one mentioned this month</span>
            </div>
        </div>`;
}

function populateMonthSelector() {
    const monthSelector = document.getElementById('month-selector');
    if (!monthSelector) return;

    // Clear existing options
    monthSelector.innerHTML = '';

    // Add options for each month
    Object.keys(visualizationData).forEach(monthDate => {
        const option = document.createElement('option');
        option.value = monthDate;
        option.textContent = formatMonthDate(monthDate);
        monthSelector.appendChild(option);
    });

    // Set initial value
    monthSelector.value = currentMonth;

    // Add change event listener
    monthSelector.addEventListener('change', handleMonthChange);
}

function handleMonthChange(event) {
    const newMonth = event.target.value;
    if (newMonth !== currentMonth) {
        // Clear existing messages
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }

        // Update current month and regenerate message queue
        currentMonth = newMonth;
        createMessageQueue(visualizationData[newMonth]);
        updateMonthTitle(newMonth);
        
        // Reset transition state
        isTransitioning = false;
        
        // Change particle flow
        noiseSeed(millis());
        
        // Reset message timing
        lastMessageTime = millis();
    }
} 