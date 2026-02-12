/**
 * Derek Staahl Portfolio - Main JavaScript
 * Handles: Mobile navigation toggle, scroll fade-in animations
 */

(function() {
  'use strict';

  // ==========================================================================
  // Mobile Navigation
  // ==========================================================================

  const navToggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav');
  const navOverlay = document.querySelector('.nav-overlay');

  if (navToggle && nav) {
    // Toggle navigation on button click
    navToggle.addEventListener('click', function() {
      const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', !isExpanded);
      nav.classList.toggle('nav--open');

      if (navOverlay) {
        navOverlay.classList.toggle('nav-overlay--visible');
      }

      // Prevent body scroll when nav is open
      document.body.style.overflow = isExpanded ? '' : 'hidden';
    });

    // Close navigation when overlay is clicked
    if (navOverlay) {
      navOverlay.addEventListener('click', function() {
        navToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('nav--open');
        navOverlay.classList.remove('nav-overlay--visible');
        document.body.style.overflow = '';
      });
    }

    // Close navigation on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && nav.classList.contains('nav--open')) {
        navToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('nav--open');
        if (navOverlay) {
          navOverlay.classList.remove('nav-overlay--visible');
        }
        document.body.style.overflow = '';
        navToggle.focus();
      }
    });

    // Close navigation when a link is clicked (for single-page sections)
    const navLinks = nav.querySelectorAll('.nav__link');
    navLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        if (window.innerWidth < 768) {
          navToggle.setAttribute('aria-expanded', 'false');
          nav.classList.remove('nav--open');
          if (navOverlay) {
            navOverlay.classList.remove('nav-overlay--visible');
          }
          document.body.style.overflow = '';
        }
      });
    });
  }

  // ==========================================================================
  // Scroll Fade-In Animation (Intersection Observer)
  // ==========================================================================

  // Check if user prefers reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!prefersReducedMotion) {
    const fadeElements = document.querySelectorAll('.fade-in');

    if (fadeElements.length > 0 && 'IntersectionObserver' in window) {
      const observerOptions = {
        root: null,
        rootMargin: '0px 0px -50px 0px',
        threshold: 0.1
      };

      const fadeObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('fade-in--visible');
            observer.unobserve(entry.target);
          }
        });
      }, observerOptions);

      fadeElements.forEach(function(element) {
        fadeObserver.observe(element);
      });
    } else {
      // Fallback: Show all elements if IntersectionObserver is not supported
      fadeElements.forEach(function(element) {
        element.classList.add('fade-in--visible');
      });
    }
  } else {
    // If user prefers reduced motion, show all elements immediately
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach(function(element) {
      element.classList.add('fade-in--visible');
    });
  }

  // ==========================================================================
  // Contact Success Message
  // ==========================================================================

  const params = new URLSearchParams(window.location.search);
  if (params.get('success') === 'true') {
    const successBanner = document.querySelector('.form-success');
    if (successBanner) {
      successBanner.hidden = false;
      successBanner.scrollIntoView({ block: 'center' });
    }
  }

  // ==========================================================================
  // Generation AI - Dynamic Episode Rendering
  // ==========================================================================

  var dynamicContainer = document.getElementById('genai-dynamic-episodes');
  if (dynamicContainer) {
    fetch('/data/episodes.json')
      .then(function(response) {
        if (!response.ok) throw new Error('Failed to fetch episodes');
        return response.json();
      })
      .then(function(data) {
        if (!data.episodes || !data.episodes.length) return;

        // Find hardcoded episode IDs already in the DOM
        var hardcoded = document.querySelectorAll('[data-episode-id]');
        var existingIds = {};
        hardcoded.forEach(function(el) {
          existingIds[el.getAttribute('data-episode-id')] = el;
        });

        // Sort episodes newest first
        var sorted = data.episodes.slice().sort(function(a, b) {
          return b.date.localeCompare(a.date);
        });

        sorted.forEach(function(ep) {
          // Hide hardcoded version if JSON has it (JSON becomes source of truth)
          if (existingIds[ep.youtubeId]) {
            existingIds[ep.youtubeId].style.display = 'none';
          }

          var article = document.createElement('article');
          article.className = 'genai-episode fade-in fade-in--visible';
          article.setAttribute('data-episode-id', ep.youtubeId);

          var html = '<div class="genai-episode__video">'
            + '<iframe src="https://www.youtube.com/embed/' + escapeAttr(ep.youtubeId) + '"'
            + ' title="' + escapeHtml(ep.title) + '"'
            + ' frameborder="0"'
            + ' allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"'
            + ' allowfullscreen loading="lazy"></iframe>'
            + '</div>'
            + '<div class="genai-episode__body">';

          if (ep.number) {
            html += '<p class="genai-episode__number">Episode ' + ep.number + '</p>';
          }

          html += '<h3 class="genai-episode__title">' + escapeHtml(ep.title) + '</h3>';

          if (ep.guest) {
            html += '<p class="genai-episode__guest">Guest: ' + escapeHtml(ep.guest) + '</p>';
          }

          if (ep.dateFormatted) {
            html += '<p class="genai-episode__date">' + escapeHtml(ep.dateFormatted) + '</p>';
          }

          if (ep.description) {
            html += '<p class="genai-episode__description">' + escapeHtml(ep.description) + '</p>';
          }

          if (ep.azfamilyUrl) {
            html += '<a href="' + escapeAttr(ep.azfamilyUrl) + '" class="genai-episode__link"'
              + ' target="_blank" rel="noopener">Watch on AZFamily</a>';
          }

          html += '</div>';
          article.innerHTML = html;
          dynamicContainer.appendChild(article);
        });
      })
      .catch(function() {
        // Fail silently -- hardcoded episodes remain visible
      });
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ==========================================================================
  // Background Logos (Twinkle Animation) - Hero and Page Headers
  // ==========================================================================

  const logos = [
    '/images/logos/arizonas-family.png',
    '/images/logos/27News.png',
    '/images/logos/3tv-azfamily.jpg',
    '/images/logos/abc10news.jpg',
    '/images/logos/CW-Logo-2015-update.webp',
    '/images/logos/KPHO_CBS_5.webp'
  ];

  // All logos eligible for twinkle animation
  const allTwinkleLogos = logos.map(() => []);

  // Function to generate logos for a container
  function generateLogos(container, rows, logosPerRow, twinkleCenterOnly) {
    if (!container) return;

    const logoPositions = [];

    for (let row = 0; row < rows; row++) {
      const logosInThisRow = row % 2 === 0 ? logosPerRow : logosPerRow - 1;
      const rowOffset = row % 2 === 0 ? 0 : 2.5;
      for (let col = 0; col < logosInThisRow; col++) {
        const baseLeftPercent = (col / logosInThisRow) * 100 + rowOffset;
        const baseTopPercent = (row / rows) * 100;
        const leftPercent = baseLeftPercent + (Math.random() - 0.5) * 4;
        const topPercent = baseTopPercent + (Math.random() - 0.5) * 3;
        const width = 38 + Math.random() * 16;
        const rotation = (Math.random() - 0.5) * 44;
        const opacity = 0.38 + Math.random() * 0.15;

        logoPositions.push({ leftPercent, topPercent, width, rotation, opacity });
      }
    }

    logoPositions.forEach((pos, index) => {
      const img = document.createElement('img');
      const typeIndex = index % logos.length;
      img.src = logos[typeIndex];
      img.alt = '';
      img.className = 'hero-logo' + (typeIndex === 0 ? ' azfamily-logo' : '');
      img.dataset.type = typeIndex;
      img.style.cssText = `
        left: ${pos.leftPercent}%;
        top: ${pos.topPercent}%;
        width: ${pos.width}px;
        transform: rotate(${pos.rotation}deg);
        opacity: ${pos.opacity};
      `;
      img.loading = 'lazy';
      container.appendChild(img);

      // Add to twinkle pool based on position criteria
      if (twinkleCenterOnly) {
        const inCenterX = pos.leftPercent >= 25 && pos.leftPercent <= 75;
        const inCenterY = pos.topPercent >= 10 && pos.topPercent <= 70;
        if (inCenterX && inCenterY) {
          allTwinkleLogos[typeIndex].push(img);
        }
      } else {
        // For smaller headers, all logos can twinkle
        allTwinkleLogos[typeIndex].push(img);
      }
    });
  }

  if (!prefersReducedMotion) {
    // Generate logos for hero section (home page)
    const heroLogosContainer = document.getElementById('hero-logos');
    if (heroLogosContainer) {
      generateLogos(heroLogosContainer, 15, 18, true);
    }

    // Generate logos for page headers (about, contact, etc.)
    const pageHeaderLogosContainer = document.getElementById('page-header-logos');
    if (pageHeaderLogosContainer) {
      generateLogos(pageHeaderLogosContainer, 5, 18, false);
    }

    // Twinkle animation system
    let currentTypeIndex = 0;
    const TWINKLE_DURATION = 1600;
    const TWINKLE_INTERVAL = 2500;

    function twinkleRandomLogo() {
      const logosOfType = allTwinkleLogos[currentTypeIndex];
      if (logosOfType.length > 0) {
        const randomIndex = Math.floor(Math.random() * logosOfType.length);
        const logo = logosOfType[randomIndex];
        logo.classList.add('twinkle');
        setTimeout(() => logo.classList.remove('twinkle'), TWINKLE_DURATION);
      }
      currentTypeIndex = (currentTypeIndex + 1) % logos.length;
    }

    // Start twinkle loop if there are any logos
    const hasLogos = allTwinkleLogos.some(arr => arr.length > 0);
    if (hasLogos) {
      setInterval(twinkleRandomLogo, TWINKLE_INTERVAL);
      twinkleRandomLogo();
    }
  }

})();
