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
    history.replaceState({}, '', '#people');
  }

  app.dom_ready = true;
  initialize_view();
}

function initialize_view() {
  if (!app.dom_ready || !app.data_loaded) {
    // not ready to populate the view. whicheven is loaded second
    // will retrigger this method.
    return;
  }

  const people = document.querySelector("#people");
  const group_template = document.querySelector("#item_group_template");
  const item_template = document.querySelector("#item_template");

  app.npcs.forEach(npc => {
    let npc_view = group_template.content.cloneNode(true);
    npc_view.querySelector(".title").innerHTML = npc.name;
    npc_view.querySelector(".additional_info").innerHTML = npc.birthday;

    let item_list = npc_view.querySelector(".items");
    npc.gifts.forEach(gift => {
      let cell_view = item_template.content.cloneNode(true);
      cell_view.querySelector(".item_title").innerHTML = gift.prop_name;
      cell_view.querySelector(".additional_item_info").innerHTML = gift.favor;
      item_list.appendChild(cell_view);
    });

    people.appendChild(npc_view);
  });
}

function main() {
  load_data(on_data_loaded);
  document.addEventListener("DOMContentLoaded", event => {
    init_app()
  });
}



main();
