let enemies = document.querySelectorAll("[id^=id_enemy_]");
const scripts = document.querySelectorAll("[id^=id_player_]");
const lowlife = document.querySelectorAll("[id^=id_lowlife_]")[0];
let attack_scripts = document.querySelectorAll("[id^=id_player_],[id^=id_lowlife_]")

const start_time = Date.now();
const attack_log = document.getElementById("id_attack_log");
const sword_icon = '<img src="/static/img/sword.svg">'
const tomb_icon = '<img src="/static/img/tomb.svg">'

function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function remove_heal_select(elm) {
    elm.classList.remove("heal-selected");
    elm.classList.add("border-0");
}

function add_heal_select(elm) {
    elm.classList.add("heal-selected");
    elm.classList.remove("border-0");
}

document.addEventListener("DOMContentLoaded", (event) => {
    lowlife.addEventListener("click", (event) => {
        add_heal_select(lowlife);
        for(let i = 0; i < scripts.length; ++i) {
            let selected_script = scripts[i]
            remove_heal_select(selected_script);
        }
    });
    for(let index = 0; index < scripts.length; ++index) {
        let script = scripts[index];
        script.addEventListener("click", (event) => {
            remove_heal_select(lowlife);
            for(let i = 0; i < scripts.length; ++i) {
                let selected_script = scripts[i]
                if (selected_script !== script) {
                    remove_heal_select(selected_script);
                } else {
                    add_heal_select(selected_script);
                }
            }
        });
    }

    main_loop();
});

async function main_loop() {
    let sum_health = 0;
    for(let index = 0; index < enemies.length; ++index) {
        let enemy = enemies[index];
        let enemy_health = enemy.querySelector(`[id^=id_health_]`);
        sum_health += parseInt(enemy_health.getAttribute("aria-valuenow"));
        if (!enemy.classList.contains("attacking")) {
            let target_index = getRandomInt(0, attack_scripts.length-1)
            attack(enemy, attack_scripts[target_index], target_index, 'player')
        }
    }
    if (sum_health === 0) {
        add_log_message(`You Won`)
        return;
    }

    sum_health = 0;
    for(let index = 0; index < scripts.length; ++index) {
        let script = scripts[index];
        let script_health = script.querySelector(`[id^=id_health_]`);
        sum_health += parseInt(script_health.getAttribute("aria-valuenow"));
        if (!script.classList.contains("attacking")) {
            let target_index = getRandomInt(0, enemies.length-1)
            attack(script, enemies[target_index], target_index, 'enemy')
        }
    }
    if (sum_health === 0) {
        add_log_message(`You Lost`)
        return;
    }
    setTimeout(main_loop, 10);
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function animate(element, duration) {
    transition.begin(element, [
        ["width", '0%', '100%']
    ], {
        duration: `${duration}s`,
        timingFunction: "linear",
        onTransitionEnd: function(element, finished) {
            if (!finished) return;
            element.style.width = "0";
        }
    });

}

async function add_log_message(message, icon = null) {
    const time = Date.now() - start_time;
    const diffMs = time % 1000;
    const diffSec = Math.floor(time / 1000); // seconds

    let newParagraph = document.createElement("DIV");
    newParagraph.classList.add("row");
    let time_col = document.createElement("DIV");
    time_col.classList.add("col-2", "text-center","my-auto");
    let icon_col = document.createElement("DIV");
    icon_col.classList.add("col-1", "text-center","my-auto");
    let message_col = document.createElement("DIV");
    message_col.classList.add("col-9");

    if (icon) {
        icon_col.innerHTML = `${icon}`;
    }
    time_col.innerHTML = `${diffSec}.${diffMs}s`;
    message_col.innerHTML = `${message}`;

    newParagraph.appendChild(time_col);
    newParagraph.appendChild(icon_col);
    newParagraph.appendChild(message_col);

    attack_log.prepend(newParagraph);
}

async function attack(source, target, target_index, type) {
    if (target.classList.contains("dead")) {
        return;
    }
    source.classList.add("attacking");
    let source_name = source.getAttribute('script_name');
    let target_name = target.getAttribute('script_name');
    let attack_progress = source.querySelector(`[id^=id_attack_value_]`);
    let wait_time = getRandomInt(1000, 3000)
    animate(attack_progress, wait_time/1000)
    sleep(wait_time).then(() => {
        let target_health_value = target.querySelector(`[id^=id_value_health_]`);

        if (target.classList.contains("dead")) {
            add_log_message(`${source_name} attacked ${target_name} who was already dead!`, `${tomb_icon}`)
            source.classList.remove("attacking");
            return;
        }

        if (source.classList.contains("dead")) {
            add_log_message(`${source_name} attacked ${target_name} but died while trying!`, `${tomb_icon}`)
            return;
        }

        let attack_strength = getRandomInt(1, 10)
        add_log_message(`${source_name} attacked ${target_name} for ${attack_strength} damage!`, `${sword_icon}`);

        let target_health = target.querySelector(`[id^=id_health_]`);
        let max_health = parseInt(target_health.getAttribute("aria-valuemax"));

        let health_result = parseInt(target_health_value.textContent) - attack_strength;
        if (health_result <= 0) {
            health_result = 0;
            if (type === 'enemy') {
                delete attack_scripts[target_index];
            } else {
                delete enemies[target_index];
            }

            target.getElementsByClassName("dead")[0].classList.remove("d-none");
            target.getElementsByClassName("alive")[0].classList.add("d-none");
            target.classList.add("dead");
        }
        let health_percent = `${parseInt((health_result / max_health)*100)}%`
        target_health_value.setAttribute("style", `width: ${health_percent}`);

        target_health_value.textContent = health_result;
        target_health.setAttribute("aria-valuenow", health_result);

        source.classList.remove("attacking");

    });

}