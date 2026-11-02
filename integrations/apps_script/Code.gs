/**
 * Mailroom Google Apps Script bridge.
 *
 * Deploy one copy per Gmail mailbox. The mailbox owner runs the script, so
 * GmailApp sends from that account.
 *
 * Script Properties:
 *   MAILROOM_SHARED_SECRET = a long random value shared with the Mailroom mailbox
 *
 * Web app deployment: execute as the owner, access to anyone with the link.
 */

function doPost(e) {
  try {
    var body = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    var expected = PropertiesService.getScriptProperties().getProperty("MAILROOM_SHARED_SECRET");
    if (!expected || body.secret !== expected) {
      return json_({ ok: false, error: "Unauthorized" });
    }

    if (body.action === "ping") {
      return json_({ ok: true, message: "Mailroom bridge is awake" });
    }

    if (body.action !== "send") {
      return json_({ ok: false, error: "Unknown action" });
    }

    if (!body.to || !body.subject || !body.body) {
      return json_({ ok: false, error: "to, subject and body are required" });
    }

    var options = {
      name: body.fromName || "Mailroom",
      replyTo: body.from || undefined
    };
    if (body.html) {
      GmailApp.sendEmail(body.to, body.subject, body.body, Object.assign({}, options, { htmlBody: body.html }));
    } else {
      GmailApp.sendEmail(body.to, body.subject, body.body, options);
    }

    return json_({
      ok: true,
      messageId: "gas-" + new Date().getTime() + "-" + Math.random().toString(36).slice(2, 10)
    });
  } catch (error) {
    return json_({ ok: false, error: String(error) });
  }
}

function json_(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
