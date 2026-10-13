/* Pequenas interações progressivas: formulários funcionam mesmo sem JavaScript. */
document
  .querySelectorAll("[data-dismiss]")
  .forEach((button) =>
    button.addEventListener("click", () => button.closest(".flash").remove()),
  );
document.querySelectorAll("form[data-confirm]").forEach((form) =>
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  }),
);
document
  .querySelectorAll("[data-focus]")
  .forEach((button) =>
    button.addEventListener("click", () =>
      document.getElementById(button.dataset.focus)?.focus(),
    ),
  );
document.querySelectorAll("[data-gallery-src]").forEach((button) =>
  button.addEventListener("click", () => {
    document.getElementById("gallery-main").src = button.dataset.gallerySrc;
  }),
);
const photoInput = document.querySelector("[data-photo-preview]");
if (photoInput) {
  const preview = document.querySelector(".composer-preview");
  let objectUrl;
  function clearPreview() {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    photoInput.value = "";
    preview.hidden = true;
    document.querySelector("[data-photo-name]").textContent = "";
  }
  photoInput.addEventListener("change", () => {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    const file = photoInput.files[0];
    if (!file) {
      clearPreview();
      return;
    }
    if (file.size > 6 * 1024 * 1024) {
      clearPreview();
      window.alert("Escolha uma foto de até 6 MB.");
      return;
    }
    objectUrl = URL.createObjectURL(file);
    preview.querySelector("img").src = objectUrl;
    preview.hidden = false;
    document.querySelector("[data-photo-name]").textContent = file.name;
  });
  document
    .querySelector("[data-clear-photo]")
    .addEventListener("click", clearPreview);
}
