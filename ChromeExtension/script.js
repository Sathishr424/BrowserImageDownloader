async function downloadImages() {
  let urls = document.querySelector("#urls").value;
  const subfolder = document.querySelector("#subfolder").value;
  if (urls.length == 0) return
  console.log("Before parsing", urls)
  try {
    urls = JSON.parse(urls)
  } catch (err) {
    console.error(err)
    return
  }

  console.log("After parsing:", urls)

  const response = await triggerPythonDaemon(urls, subfolder);

  const messageElement = document.querySelector("#message");
  messageElement.style.display = "block"
  if (response) {
    messageElement.innerHTML = "Downloading in progress check the configured downlaod folder"
  } else {
    messageElement.innerHTML = "Something went wrong, downloading failed"
  }
}

function triggerPythonDaemon(urls, subfolder) {
  return new Promise((resolve, reject) => {
    fetch("http://127.0.0.1:8766/download_images", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({urls, ...(subfolder.length > 0 ? {subfolder} : {})}),
    })
      .then(() => resolve(true))
      .catch((err) => {
        console.error(err);
        return resolve(false);
      });
  })
}

document
    .getElementById("download-btn")
    .addEventListener("click", downloadImages);
