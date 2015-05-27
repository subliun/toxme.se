function sc_showFailureOnUI(s) {
    "use strict";
    document.getElementById("lookup_results").style.display = "none";
    var message = document.getElementById("lookup_error");
    message.style.display = "block";
    message.textContent = s;
}

function sc_errorStringFromCode(ec) {
    "use strict";
    switch (ec) {
    case -41:
        return "Lookup failed: unspecified error.";
    case -42:
        return "Lookup failed: user not found.";
    case -43:
        return "Lookup failed: internal error! Please report it on GitHub.";
    case -3:
        return "Lookup failed: the address wasn't valid.";
    }
}

function sc_showResultOnUI(payload) {
    "use strict";
    var message, source, sigbox, sname;
    document.getElementById("lookup_error").style.display = "none";
    message = document.getElementById("lookup_results");
    message.style.display = "block";
    document.getElementById("lu_oname").textContent = payload.name;
    document.getElementById("lu_regdomain").textContent = payload.regdomain;
    if (payload.source === 1) {
        source = "local user";
    } else {
        source = "remote user";
    }
    document.getElementById("lu_stype").textContent = source;
    document.getElementById("lu_rectype").textContent = payload.version;
    if (payload.public_key.length === 64) {
        document.getElementById("results").className = "v2";
        document.getElementById("lu_user_pk").textContent = payload.public_key;
    } else {
        document.getElementById("results").className = "v1";
        document.getElementById("lu_user_id").textContent = payload.public_key;
    }
    sigbox = document.getElementById("lu_user_sig");
    sname = encodeURIComponent(payload.name);
    sigbox.textContent = payload.verify.detail;
    sigbox.className = payload.verify.status === 1 ? "good"
                       : (payload.verify.status === 2 ? "bad" : "undecided");
    document.getElementById("lu_user_link").href = "/u/" + sname;
}

function sc_lookupStatusDidChange(sender) {
    "use strict";
    var respload, ec
    if (sender.readyState === 4) {
        try {
            respload = JSON.parse(sender.responseText);
        } catch (e) {
            respload = null;
        }

        if (sender.status !== 200) {
            if (respload && (ec = parseInt(respload.c, 10))) {
                sc_showFailureOnUI(sc_errorStringFromCode(ec));
            } else {
                sc_showFailureOnUI("Lookup failed: server responded \
                                    with status code " + sender.status);
            }
            return;
        }

        sc_showResultOnUI(respload);
    }
}

function sc_performSearch(e) {
    "use strict";
    // Check if the user pressed enter.
    if (e.type === "keydown" && e.keyCode !== 13)
            return;

    var query, xhr;
    query = document.getElementById("search_text").value.trim();
    if (query === "")
        return;
    window.searchIsRunning = 1
    xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        sc_lookupStatusDidChange(xhr);
    }
    xhr.open("POST", "/api", true);
    xhr.send(JSON.stringify({
        "action": 3,
        "name": query,
    }));
    sc_showFailureOnUI("Please wait...")
}

function sc_init() {
    "use strict";
    var qbox = document.getElementById("search_text");
    qbox.value = window.location.hash.substring(1);
    document.getElementById("search_go").addEventListener(
        "click", sc_performSearch, 1
    );
    document.getElementById("search_text").addEventListener(
        "keydown", sc_performSearch, 1
    );
}
