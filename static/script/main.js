// sidebar toggle
function toggleSidebar() {
  document.body.classList.toggle("collapsed");
}

// timer
let timeLimit = 300; 
let timeLeft = timeLimit;

function updateTimer() {
    document.getElementById("timer").textContent = timeLeft + " seconds";

    if (timeLeft <= 0) {
        // timer end → redirect to voting page
        window.location.href = "/voting_start";
    }
    timeLeft--;
}

setInterval(updateTimer, 1000);

// timer voting screen
let votingTimeLeft = 300; // example: 5 min = 300 sec

function updateVotingTimer() {
    let minutes = Math.floor(votingTimeLeft / 60);
    let seconds = votingTimeLeft % 60;
    document.getElementById("voting_timer_display").textContent =
        minutes + "m " + seconds + "s";

    if (votingTimeLeft <= 0) {
        clearInterval(timerInterval);
        alert("Voting time over!");
        // redirect ya disable voting
        window.location.href = "/results"; // ya jahan result dikha rahe ho
    }
    votingTimeLeft--;
}

let timerInterval = setInterval(updateVotingTimer, 1000);