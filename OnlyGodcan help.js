const panel = document.getElementById("resultPanel");

panel.style.display = "block";
panel.style.visibility = "visible";
panel.style.opacity = "1";
panel.style.position = "relative";
panel.style.zIndex = "9999";

console.log("RESULT PANEL:", panel);
console.log("DISPLAY:", getComputedStyle(panel).display);
console.log("VISIBILITY:", getComputedStyle(panel).visibility);
console.log("OPACITY:", getComputedStyle(panel).opacity);
