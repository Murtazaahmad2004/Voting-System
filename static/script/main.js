// confirmation popup
function confirmDelete() {
  return confirm("Are you sure you want to delete this record?");
}

// Sidebar toggle
function toggleSidebar() {
  if(window.innerWidth <= 992) {
    document.getElementById("sidebar").classList.toggle("show");
  } else {
    document.body.classList.toggle("collapsed");
  }
}

// Rainbow generator
function getRainbowColors(count) {
  const colors = [];
  for (let i = 0; i < count; i++) {
    const hue = Math.floor((i / count) * 360); // spread colors across 360deg
    colors.push(`hsl(${hue}, 70%, 50%)`);
  }
  return colors;
}

// Candidate Votes Chart
fetch("/chart/votes")
  .then((res) => res.json())
  .then((data) => {
    data.datasets[0].backgroundColor = getRainbowColors(data.labels.length);
    new Chart(document.getElementById("votesChart"), {
      type: "bar",
      data: data,
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: "Total Votes per Candidate" },
        },
      },
    });
  });

// Party Votes Chart
fetch("/chart/parties")
  .then((res) => res.json())
  .then((data) => {
    data.datasets[0].backgroundColor = getRainbowColors(data.labels.length);
    new Chart(document.getElementById("partyChart"), {
      type: "pie",
      data: data,
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" },
          title: { display: true, text: "Total Votes by Party" },
        },
      },
    });
  });
