const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const result = document.getElementById("result");

navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
  video.srcObject = stream;
});

function capture() {
  const ctx = canvas.getContext("2d");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0);
  return canvas.toDataURL("image/jpeg");
}

async function authUser() {
  const username = document.getElementById("username").value.trim();
  if (!username) return alert("Foydalanuvchi nomini kiriting!");

  const image = capture();

  const res = await fetch("/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, image }),
  });

  const data = await res.json();
  result.textContent = data.message;

  if (data.success && data.message.includes("kirdi")) {
    setTimeout(() => window.location.href = "/success", 1500);
  }
}
