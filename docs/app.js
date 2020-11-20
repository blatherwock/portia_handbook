const app = {
  view_loaded: false,
  data_loaded: false,
  dom_ready: false,
}

function load_data(on_data_loaded) {
  // Load static json data files needed for site
  let data_loaded_count = 0;
  const data_sources = [['data/npcs.json', 'npcs'],
                        ['data/props.json', 'props'],
                        ['data/gifts.json', 'gifts']]

  data_sources.forEach(source => {
    let [source_url, source_name] = source;
    fetch(source_url)
      .then(response => response.json())
      .then(json => {
        app[source_name] = json
        if (++data_loaded_count == data_sources.length) {
          on_data_loaded();
        }
      })
      .catch(err => console.log(err));
  })
}

function on_data_loaded() {
  const id_reducer = (acc, curr) => {
    curr.gifts = [];
    acc[curr.id] = curr;
    return acc
  };
  const people_by_id = app.npcs.reduce(id_reducer, {});
  const items_by_id = app.props.reduce(id_reducer, {});

  app.gifts.forEach(gift => {
    people_by_id[gift['npc']].gifts.push(gift);
    items_by_id[gift['prop']].gifts.push(gift);
  });

  const gift_sorter = (a,b) => {
    const diff = b.favor - a.favor;
    if (diff != 0)
      return diff;
    else
      return a.prop_name < b.prop_name;
  };

  app.npcs.forEach(npc => npc.gifts.sort(gift_sorter));
  app.props.forEach(prop => prop.gifts.sort(gift_sorter));

  app.data_loaded = true;
  initialize_view();
}

function init_app() {
  // on initial load, show the 'people' tab.
  if (location.hash === "") {
    history.replaceState({}, "", "#people");
  }

  document.querySelector("#filter_relics").addEventListener("click", event => {
    document.querySelector("#people .results").classList.toggle('hide-relics');
  });
  document.querySelector("#filter_cooking").addEventListener("click", event => {
    document.querySelector("#people .results").classList.toggle('hide-cookables');
  });
  document.querySelector("#filter_ack_cooking").addEventListener("click", event => {
    document.querySelector("#people .results").classList.toggle('hide-cookables_ack');
  });
  document.querySelector("#filter_universals").addEventListener("click", event => {
    document.querySelector("#people .results").classList.toggle('hide-universals');
  });
  document.querySelector("#filter_disliked").addEventListener("click", event => {
    document.querySelector("#people .results").classList.toggle('hide-dislikes');
  });
  document.querySelector("#filter_onlyselected").addEventListener("click", event => {
    document.querySelector("#people .results").classList.toggle('only-selected');
  });


  app.dom_ready = true;
  initialize_view();
}

function initialize_view() {
  if (!app.dom_ready || !app.data_loaded) {
    // not ready to populate the view. whicheven is loaded second
    // will retrigger this method.
    return;
  }

  const people = document.querySelector("#people .results");
  const group_template = document.querySelector("#item_group_template");
  const item_template = document.querySelector("#item_template");

  app.npcs.forEach(npc => {
    const npc_view = group_template.content.cloneNode(true);
    npc_view.querySelector(".group_icon").src = "images/npcs/" + npc.icon + '.png';
    npc_view.querySelector(".title").innerHTML = npc.name;
    npc_view.querySelector(".additional_info").innerHTML = npc.birthday;

    const item_list = npc_view.querySelector(".items");
    npc.gifts.forEach(gift => {
      const cell_view = item_template.content.cloneNode(true);
      cell_view.querySelector(".item_title").innerHTML = gift.prop_name;
      cell_view.querySelector(".item_icon").src = "images/items/" + gift.prop_icon + '.png';
      cell_view.querySelector(".additional_item_info").innerHTML = gift.favor;


      const gift_level_class = "gift_level-" + gift.gift_level.toLowerCase();
      const gift_prop_class = "gift_prop-" + gift.prop_type.toLowerCase();
      const gift_universal_class = "gift_uni-" + gift.prop_universality.toLowerCase();
      const gift_dislike_class = parseInt(gift.favor, 10) <= 0 ? "gift_dislike" : "";
      const classes = [gift_level_class, gift_prop_class, gift_universal_class, gift_dislike_class];
      cell_view.firstElementChild.className = classes.join(" ");

      item_list.appendChild(cell_view);
    });
    people.appendChild(npc_view);

  });

  const all_items = document.querySelectorAll(".items li");
  all_items.forEach(item => {
    item.addEventListener("click", event => {
      item.classList.toggle("selected");
    })
  });
}

function main() {
  load_data(on_data_loaded);
  document.addEventListener("DOMContentLoaded", event => {
    init_app()
  });
}



main();
