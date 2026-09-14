// ============================================================
// POMODORO TIMER
// ============================================================

const modeButtons = document.querySelectorAll(".mode-btn");
const timerText = document.getElementById("timerText");
const modeLabel = document.getElementById("modeLabel");
const ringProgress = document.getElementById("ringProgress");
const startBtn = document.getElementById("startBtn");
const pauseBtn = document.getElementById("pauseBtn");
const resetBtn = document.getElementById("resetBtn");
const sessionCountEl = document.getElementById("sessionCount");
const todayMinutesEl = document.getElementById("todayMinutes");

const DURATIONS = {
  focus: 25 * 60,
  short_break: 5 * 60,
  long_break: 15 * 60,
};

const MODE_LABELS = {
  focus: "Focus Session",
  short_break: "Short Break",
  long_break: "Long Break",
};

const RING_CIRCUMFERENCE = 2 * Math.PI * 135; // r=135 from the SVG

let currentMode = "focus";
let secondsRemaining = DURATIONS.focus;
let timerInterval = null;
let isRunning = false;
let focusStreak = 0;

ringProgress.style.strokeDasharray = RING_CIRCUMFERENCE;

// ============================================================
// NOTIFICATION PERMISSION
// ============================================================

if ("Notification" in window && Notification.permission === "default") {
  Notification.requestPermission();
}

function notifyTimerFinished(mode) {
  const messages = {
    focus: "🍅 Focus session complete! Time for a break.",
    short_break: "☕ Break's over! Ready to focus again?",
    long_break: "🌿 Long break finished! Let's get back to it.",
  };

  if ("Notification" in window && Notification.permission === "granted") {
    new Notification("Pomodoro Timer", {
      body: messages[mode],
    });
  }
}

// ============================================================
// DISPLAY HELPERS
// ============================================================

function updateDisplay() {
  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  timerText.textContent = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  const total = DURATIONS[currentMode];
  const progress = secondsRemaining / total;
  const offset = RING_CIRCUMFERENCE * (1 - progress);
  ringProgress.style.strokeDashoffset = offset;
}

function setMode(mode) {
  currentMode = mode;
  secondsRemaining = DURATIONS[mode];
  modeLabel.textContent = MODE_LABELS[mode];

  ringProgress.classList.remove(
    "mode-focus",
    "mode-short_break",
    "mode-long_break",
  );
  ringProgress.classList.add(`mode-${mode}`);

  updateDisplay();

  modeButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.mode === mode);
  });

  pauseTimer();
  startBtn.disabled = false;
  startBtn.textContent = "Start";
}

// ============================================================
// TIMER CONTROLS
// ============================================================

function startTimer() {
  if (isRunning) return;

  isRunning = true;
  startBtn.disabled = true;
  pauseBtn.disabled = false;

  timerInterval = setInterval(() => {
    secondsRemaining--;
    updateDisplay();

    if (secondsRemaining <= 0) {
      clearInterval(timerInterval);
      isRunning = false;
      onTimerFinished();
    }
  }, 1000);
}

function pauseTimer() {
  clearInterval(timerInterval);
  isRunning = false;
  startBtn.disabled = false;
  startBtn.textContent = "Resume";
  pauseBtn.disabled = true;
}

function resetTimer() {
  pauseTimer();
  secondsRemaining = DURATIONS[currentMode];
  startBtn.textContent = "Start";
  updateDisplay();
}

// ============================================================
// ON FINISH
// ============================================================

async function onTimerFinished() {
  notifyTimerFinished(currentMode);

  const durationMinutes = DURATIONS[currentMode] / 60;

  await saveSession(currentMode, durationMinutes);

  if (currentMode === "focus") {
    focusStreak++;

    if (focusStreak % 4 === 0) {
      setMode("long_break");
    } else {
      setMode("short_break");
    }
  } else {
    setMode("focus");
  }

  startBtn.disabled = false;
  pauseBtn.disabled = true;
}

// ============================================================
// SAVE SESSION TO BACKEND
// ============================================================

async function saveSession(sessionType, durationMinutes) {
  try {
    const response = await fetch(window.pomodoroConfig.saveSessionUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": window.pomodoroConfig.csrfToken,
      },
      body: JSON.stringify({
        session_type: sessionType,
        duration_minutes: durationMinutes,
      }),
    });

    const data = await response.json();

    if (data.success) {
      sessionCountEl.textContent = data.session_count;
      todayMinutesEl.textContent = data.today_minutes;
    }
  } catch (error) {
    console.error("❌ Failed to save Pomodoro session:", error);
  }
}

// ============================================================
// EVENT LISTENERS
// ============================================================

modeButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    setMode(btn.dataset.mode);
  });
});

startBtn.addEventListener("click", startTimer);
pauseBtn.addEventListener("click", pauseTimer);
resetBtn.addEventListener("click", resetTimer);

// ============================================================
// INIT
// ============================================================

setMode("focus");
pauseBtn.disabled = true;
