# ReLEAF vision section: current vs student versions

A comparison page for the last section of the ReLEAF (GEMS Taiwan, iGEM 2026)
homepage, "Every farmer a biomanufacturer."

- **A** is the section on the wiki now: a generated valley, night to first light.
- **B** is the student's hand-drawn valley (2 October 2026), relit from night to
  first light. Each reactor lights its own painted field as the camera pulls back.

- **C** is B with farm details added: houses, trees, farmers and crops. These
  are drawn by code (AI-assisted) in the manner of her painting; they are not
  her drawing.

- **D** is C refined: one scroll takes it from the first field to the whole
  valley while the sun rises; the picture is sharper; her own reactor drawing
  stands at every dot; paddies, orchards and more are added (also by code).

- **E (v5)** is D laid out to a far horizon. Her field plane is re-projected
  in perspective and continued, with her own fields tiled, to a hazy skyline;
  her mountains are pushed back into layered ridges under a taller sky; her
  hill and her cliff frame the view from the front corners; reactor lights run
  out to the horizon. Every pixel is hers or D's, re-placed by
  `build/vision-student-e.py` (in this repository).

- **F (v6)** is A's composition painted in her manner. The scene is A's (the
  wiki's generator, `build/valley_a.py`: camera, field grid, river, hills,
  ridges, farms); nothing of A's rendering is kept. Code paints every surface
  the way she paints: her field colours with soft edges and pale paths, crop
  dots and furrows, her olive hills with contour folds, her river, her
  mountains and sky, and her houses, trees, greenhouses, farmers and truck
  (cut from D by `build/extract_sprites.py`) standing in A's places
  (`build/vision-student-f.py`).

A pill bar at the foot of the screen switches between the versions (the arrow
keys step through them).

Scroll through each section to see it play. Her five original frames are at the
bottom of the page. The site menu at the top links to wiki pages that are not
part of this repository.

Layers for B are built by `build/vision-student.py` in the wiki repository.
