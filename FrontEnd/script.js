const songsTabRNR = document.getElementById('RockNRollSongs')
const RockNRollSongsBtn = document.getElementById('RockNRollPlaylist');
const closeBtn = document.getElementById('closeBtn')

RockNRollSongsBtn.addEventListener('click', () => {
  songsTabRNR.style.display = 'flex'; //show songs
})

closeBtn.addEventListener('click', () => {
  songsTabRNR.style.display = 'none'; //hides songs
})

window.addEventListener('click', (e) => {
  if(e.target === songsTabRNR)
  {
    songsTabRNR.style.display = 'none'; //hides songs upon clicking anywhere else if it is open
  }
})

async function loadPlaylist() {
const folderId = 'YOUR_FOLDER_ID';
const res = await fetch(`/api/files?folderId=${folderId}&audioOnly=true`);
const data = await res.json();
console.log(data.files); // [{ name, url, ... }]
// render into your player here
}
loadPlaylist();
