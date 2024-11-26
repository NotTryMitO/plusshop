// links/buttons starts
document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.button');
    buttons.forEach(button => {
        button.addEventListener('click', event => {
            window.open('https://discord.com/channels/1307354161737629696/1307362255532200086', '_blank');
        });
    });
  });

  // links/buttons ends
  // smoth scroll starts
  function smoothScrollTo(target) {
    const startPosition = window.scrollY;
    const targetPosition = target.getBoundingClientRect().top + startPosition;
    const distance = targetPosition - startPosition;
    const duration = 800;
    const startTime = performance.now();

    function animation(currentTime) {
      const elapsedTime = currentTime - startTime;
      const progress = Math.min(elapsedTime / duration, 1);
      const ease = easeInOutCubic(progress);
      window.scrollTo(0, startPosition + distance * ease);

      if (progress < 1) {
        requestAnimationFrame(animation);
      }
    }

    function easeInOutCubic(t) {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    requestAnimationFrame(animation);
  }

  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      smoothScrollTo(target);
    });
  });
  //smoth scroll ends
  
  //discord
  document.getElementById("discord-login").onclick = function() {
    window.location.href = "/discord/login";
  };
  //discord